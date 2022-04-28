import time
from typing import Optional

from baselines import configurations
from baselines.data_class import Data
from baselines.evaluator import EvaluatorSingle, EvaluatorCompeting
from baselines.models import CPH, DeepHitSingleEvent, DeepHitCompeting, DeepSurv, DSM, PCHazard, RSF
from baselines.utils import export_results, update_run


def run_experiment(dataset_name: str, model_name: str, num_runs=10, event_to_censor: Optional[str]=None):
    '''
    trains the model on the given dataset 
    '''
    censor_event = True if event_to_censor else False
    print('Censoring event:', censor_event)
    
    # intialize configuration
    config = getattr(configurations, f'{model_name}_{dataset_name}')
    config.model = model_name


    # add event to censor and to keep into config
    if censor_event:
        config.event_to_censor = event_to_censor
        event_to_keep = '0' if config.event_to_censor == 'event_1' else '1'
        config.event_to_keep = 'event_' + event_to_keep
    
    try:
        event_name = '-' + config.event_to_keep
    except AttributeError:
        event_name = ''
    print(f'Running {config.model}{event_name} on {dataset_name}')

    # config.epochs=1


    # get corresponding model
    if config.model == 'CPH':
        Model = CPH
    elif config.model == 'DeepHit':
        if config.data == 'seer':
            Model = DeepHitCompeting
        else:
            Model = DeepHitSingleEvent
    elif config.model == 'DeepSurv':
        Model = DeepSurv
    elif config.model == 'DSM':
        Model = DSM
    elif config.model == 'PCHazard':
        Model = PCHazard
    elif config.model == 'RSF':
        Model = RSF
    else:
        raise('Wrong model name provided')

    # get corresponding evaluator
    if (config.model == 'DeepHit' or config.model == 'DSM') and config.data == 'seer':
        Evaluator = EvaluatorCompeting
    else:
        Evaluator = EvaluatorSingle

    # store each run in list
    runs_list = []
    for i in range(num_runs):
        print(f'Run {i+1}/{num_runs}')

        # load data
        data = Data(config, censor_event)
        # print(config)

        # initalize model
        m = Model(config)

        # train model
        train_time_start = time.time()
        m.train(data)
        train_time_finish = time.time()

        # calcuate metrics
        evaluator = Evaluator(data, m, config)
        run = evaluator.eval()
        run = update_run(run, train_time_start, train_time_finish, m.epochs_trained)

        runs_list.append(run)

    export_results(runs_list, config)


def main():
    # models that require an event to be censored for competing events
    cause_specific_models = set(['CPH', 'DeepSurv', 'PCHazard', 'RSF'])  
    number_runs = 1

    datasets = ['metabric', 'support', 'seer']
    # datasets = ['seer']
    models = ['DeepHit', 'DeepSurv', 'DSM', 'PCHazard', 'RSF']
    # models = ['DSM']

    for model_name in models:
        for dataset_name in datasets:
            if dataset_name == 'seer' and model_name in cause_specific_models:
                run_experiment(dataset_name, model_name, number_runs, event_to_censor='event_0')
                run_experiment(dataset_name, model_name, number_runs, event_to_censor='event_1')
            else:
                run_experiment(dataset_name, model_name, number_runs)


if __name__ == '__main__':
    main()