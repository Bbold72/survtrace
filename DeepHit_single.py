from collections import defaultdict
from easydict import EasyDict
import numpy as np
from pathlib import Path
import pickle
from sksurv.metrics import concordance_index_ipcw
import time

import torchtuples as tt # Some useful functions

from pycox.models import DeepHitSingle

from baselines.data_class import Data
from baselines.models import simple_dln

num_runs = 1
datasets = ['metabric', 'support']

# define the setup parameters
config_metabric = EasyDict({
    'data': 'metabric',
    'horizons': [.25, .5, .75],
    'batch_size': 64,
    'learning_rate': 0.01,
    'epochs': 100,
    'hidden_size': 32,
    'dropout': 0.1
})
config_support = EasyDict({
    'data': 'support',
    'horizons': [.25, .5, .75],
    'batch_size': 128,
    'learning_rate': 0.01,
    'epochs': 100,
    'hidden_size': 32,
    'dropout': 0.1
})

for dataset_name in datasets:
    print('Running DeepHit on ' + dataset_name)

    config = config_metabric if dataset_name == 'metabric' else config_support
    config.model = 'DeepSurv'

    # store each run in list
    runs_list = []

    for i in range(num_runs):

        # load data
        data = Data(config)

        # define neural network
        net = simple_dln(config)

        # initialize model
        model = DeepHitSingle(net, tt.optim.Adam, alpha=0.2, sigma=0.1, duration_index=np.array(config['duration_index'], dtype='float32'))
        model.optimizer.set_lr(config.learning_rate)
        callbacks = [tt.callbacks.EarlyStopping(patience=20)]

        # train model
        train_time_start = time.time()
        log = model.fit(data.x_train, data.y_train, config.batch_size, config.epochs, callbacks, val_data=data.val_data)
        train_time_finish = time.time()


        # calcuate metrics
        def evaluator(df, train_index, model, test_set, config, val_batch_size=None):
            df_train_all = df.loc[train_index]
            get_target = lambda df: (df['duration'].values, df['event'].values)
            durations_train, events_train = get_target(df_train_all)
            et_train = np.array([(events_train[i], durations_train[i]) for i in range(len(events_train))],
                            dtype = [('e', bool), ('t', float)])
            times = config['duration_index'][1:-1]
            horizons = config['horizons']

            df_test, df_y_test = test_set
            surv = model.predict_surv(df_test, batch_size=val_batch_size)
            risk = np.array((1 - surv))
            
            durations_test, events_test = get_target(df_y_test)
            et_test = np.array([(events_test[i], durations_test[i]) for i in range(len(events_test))],
                        dtype = [('e', bool), ('t', float)])
            metric_dict = defaultdict(list)
            cis = []
            for i, _ in enumerate(times):
                cis.append(
                    concordance_index_ipcw(et_train, et_test, estimate=risk[:, i], tau=times[i])[0]
                    )
                metric_dict[f'{horizons[i]}_ipcw'] = cis[i]

            for horizon in enumerate(horizons):
                print(f"For {horizon[1]} quantile,")
                print("TD Concordance Index - IPCW:", cis[horizon[0]])
            
            return metric_dict

        run = evaluator(data.df, data.df_train.index, model, (data.x_test, data.df_y_test), config=config)
        run['train_time'] = train_time_finish - train_time_start
        run['epochs_trained'] = log.epoch
        run['time_per_epoch'] =  run['train_time'] / run['epochs_trained']

        runs_list.append(run)

    file_name = 'DeepHit' + '_' + config['data'] + '.pickle'
    with open(Path('results', file_name), 'wb') as f:
        pickle.dump(runs_list, f)

