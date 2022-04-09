from easydict import EasyDict
from collections import defaultdict
import numpy as np
from pathlib import Path
import pickle
from sksurv.metrics import concordance_index_ipcw
import time

import torchtuples as tt # Some useful functions

from pycox.models import CoxPH

from baselines.data_class import Data
from baselines.models import simple_dln
from baselines.evaluator import Evaluator


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
    print('Running DeepSurv on ' + dataset_name)

    config = config_metabric if dataset_name == 'metabric' else config_support
    config.model = 'DeepSurv'

    # store each run in list
    runs_list = []

    for i in range(num_runs):

        # load data
        data = Data(config)

        # define neural network
        config.out_feature = 1   # need to overwrite value set in load_data
        net = simple_dln(config)

        # initialize model
        model = CoxPH(net, tt.optim.Adam)
        model.optimizer.set_lr(config.learning_rate)
        callbacks = [tt.callbacks.EarlyStopping(patience=20)]

        # train model
        train_time_start = time.time()
        log = model.fit(data.x_train, data.y_train, config.batch_size, config.epochs, callbacks, verbose=True, val_data=data.val_data, val_batch_size=config.batch_size)
        train_time_finish = time.time()

        # calcuate metrics
        evaluator = Evaluator(data, model, config, offset=0)
        run = evaluator.eval()
        run['train_time'] = train_time_finish - train_time_start
        run['epochs_trained'] = log.epoch
        run['time_per_epoch'] =  run['train_time'] / run['epochs_trained']

        runs_list.append(run)

    file_name = 'DeepSurv' + '_' + config['data'] + '.pickle'
    with open(Path('results', file_name), 'wb') as f:
        pickle.dump(runs_list, f)

