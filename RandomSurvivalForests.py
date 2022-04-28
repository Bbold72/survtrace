import time

from baselines.data_class import Data
from baselines.evaluator import EvaluatorRSF
from baselines.utils import export_results, update_run
from baselines import configurations
from baselines.models import RSF


num_runs = 10
datasets = ['metabric', 'support', ('seer', 'event_0'), ('seer', 'event_1')]
# datasets = ['metabric', 'support']
# # datasets = [('seer', 'event_0'), ('seer', 'event_1')]
# datasets = [('seer', 'event_1')]
model_name = 'RSF'

for dataset_name in datasets:
    if type(dataset_name) == tuple:
        dataset_name, event_to_censor = dataset_name
        censor_event = True
    else:
        censor_event = False

    config = getattr(configurations, f'{model_name}_{dataset_name}')
    config.model = model_name
    print(f'Running {config.model} on {dataset_name}')
    print(config)


    if censor_event:
        config.event_to_censor = event_to_censor
        event_to_keep = '0' if config.event_to_censor == 'event_1' else '1'
        config.event_to_keep = 'event_' + event_to_keep


    try:
        event_name = '-' + config.event_to_keep
    except AttributeError:
        event_name = ''

    print(f'Running {config.model}{event_name} on {dataset_name}')

    # store each run in list
    runs_list = []

    for i in range(num_runs):

        # load data
        data = Data(config, censor_event)
        
        # initialize model
        model = RSF(config)

        # train model
        train_time_start = time.time()
        model = model.train(data)
        train_time_finish = time.time()        

        # calcuate metrics
        evaluator = EvaluatorRSF(data, model, config)
        run = evaluator.eval()
        run = update_run(run, train_time_start, train_time_finish, config.epochs)
        runs_list.append(run)

    export_results(runs_list, config)

