import os
import sh
import importlib
from io import StringIO
import yaml
from .util import build_run_vars


def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """

    config_keys = [
        {'pi_lint_pipe_vars': 'pi_lint.pi_lint'},
        {'pi_validate_pipe_vars': 'pi_validate.pi_validate'},
        {'file_config': 'pi_validate.pi_files'},
        {'ci': 'pi_ci_gitlab.pi_ci_gitlab'}
    ]


    validation_list = []
    for run_vars in build_run_vars(request):
        pipe_configs = yaml.load(run_vars)
        for pipe, config in pipe_configs.items():
            new_dict = {pipe:config}
            validation_list.append(new_dict)

    validation_results = []
    for config in validation_list:
        for key, value in config.items():
            if key in {key for dict in config_keys for key in dict.keys()} and key != 'ci':
                temp_dict = {key:value}
                [module_name] = [config_key[key] for config_key in config_keys if key in config_key.keys()]
                validation_module = getattr(importlib.import_module(f'function.validations.pipes.{module_name}'), 'validate')
                result = validation_module(temp_dict)
                if result == True:
                    validation_results.append({key: {'errors': False}})
                else:
                    validation_results.append({key: {'errors': str(result.messages)}})
            if key =='ci':
                ci_result = False
                ci_results = []
                for ci_key, ci_value in value['ci_provider_config'].items():
                    if ci_key == 'stages':
                        validation_module = getattr(importlib.import_module('function.validations.pipes.pi_gitlab_ci.pi_gitlab_ci'), 'validate')
                        result = validation_module(ci_key.capitalize(), {'stages':ci_value})
                        if result == True:
                            ci_results.append({ci_key: {'errors': False}})
                        else:
                            ci_results.append({ci_key: {'errors': str(result.messages)}})
                    elif ci_key == 'include':
                        temp_dict = {ci_key:ci_value}
                        validation_module = getattr(importlib.import_module('function.validations.pipes.pi_gitlab_ci.pi_gitlab_ci'), 'validate')
                        result = validation_module(ci_key.capitalize(), temp_dict)
                        if result == True:
                            ci_results.append({ci_key:{'errors': False}})
                        else:
                            ci_results.append({ci_key:{'errors': str(result.messages)}})

                for item in ci_results:
                    for value in item.values():
                        if value['errors'] == False:
                            ci_result = {'errors': False}
                        else:
                            ci_result = {'errors': ci_results}

                validation_results.append({key:ci_result})

    return validation_results


