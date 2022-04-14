from pathlib import Path
import pickle

def export_results(results_list, config):

    if config.data == 'seer' and config.model == 'PCHazard':
        event_name = '_' + config.event_to_keep
    else:
        event_name = ''

    file_name = config['model'] + '_' + config['data'] + f'{event_name}.pickle'
    with open(Path('results', file_name), 'wb') as f:
        pickle.dump(results_list, f)

def update_run(run_dict, train_time_start, train_time_finish, epochs_trained):
    run_dict['train_time'] = train_time_finish - train_time_start
    run_dict['epochs_trained'] = epochs_trained
    run_dict['time_per_epoch'] =  run_dict['train_time'] / run_dict['epochs_trained']
    return run_dict