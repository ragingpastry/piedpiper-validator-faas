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

    validation_list = []
    for run_vars in build_run_vars(request):
        pipe_configs = yaml.load(run_vars)
        for pipe, config in pipe_configs.items():
            new_dict = {pipe:config}
            validation_list.append(new_dict)

    validation_results = []
    for config in validation_list:
        for key, value in config.items():
            if key == 'pi_lint_pipe_vars':
                temp_dict = {key:value}
                validation_module = getattr(importlib.import_module('function.validations.pipes.pi_lint.pi_lint'), 'validate')
                result = validation_module(temp_dict)
                if result == True:
                    validation_results.append({key:True})
                else:
                    result = validation_results.append({key:str(result.messages)})
            if key == 'pi_validate_pipe_vars':
                temp_dict = {key:value}
                validation_module = getattr(importlib.import_module('function.validations.pipes.pi_validate.pi_validate'), 'validate')
                result = validation_module(temp_dict)
                if result == True:
                    result = validation_results.append({key:True})
                else:
                    result = validation_results.append({key:str(result.messages)})
            if key == 'file_config':
                temp_dict = {key:value}
                validation_module = getattr(importlib.import_module('function.validations.pipes.pi_validate.pi_files'), 'validate')
                result = validation_module(temp_dict)
                if result == True:
                    result = validation_results.append({key:True})
                else:
                    result = validation_results.append({key:str(result.messages)})
            if key =='ci':
                ci_result = False
                ci_results = []
                for ci_key, ci_value in value['ci_provider_config'].items():
                    if ci_key == 'stages':
                        validation_module = getattr(importlib.import_module('function.validations.pipes.pi_gitlab_ci.pi_gitlab_ci'), 'validate')
                        result = validation_module(ci_key.capitalize(), {'stages':ci_value})
                        if result == True:
                            result = ci_results.append({ci_key:True})
                        else:
                            result = ci_results.append({ci_key:str(result.messages)})
                    elif ci_key == 'include':
                        temp_dict = {ci_key:ci_value}
                        validation_module = getattr(importlib.import_module('function.validations.pipes.pi_gitlab_ci.pi_gitlab_ci'), 'validate')
                        result = validation_module(ci_key.capitalize(), temp_dict)
                        if result == True:
                            result = ci_results.append({ci_key:True})
                        else:
                            result = ci_results.append({ci_key:str(result.messages)})

                for item in ci_results:
                    for value in item.values():
                        if value == True:
                            ci_result = True
                        else:
                            ci_result = ci_results

                validation_results.append({key:ci_result})

    #raise ValueError(validation_results)
    return validation_results
    #return '\n'.join([yaml.dump(result) for result in validation_results])


