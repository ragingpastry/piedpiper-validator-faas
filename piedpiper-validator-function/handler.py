import importlib
import tempfile
import os
import git
import yaml
from .util import build_run_vars


def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """

    config_keys = [
        {'pi_style_pipe_vars': ['pi_style', 'pi_style']},
        {'pi_validate_pipe_vars': ['pi_validate', 'pi_validate']},
        {'file_config': ['pi_validate', 'pi_files']},
        {'ci': ['pi_ci_gitlab', 'pi_ci_gitlab']}
    ]

    validation_repo = 'https://github.com/AFCYBER-DREAM/piedpiper-project-validations.git'

    validation_results = []
    validation_dict = yaml.safe_load(build_run_vars(request))
    try:
        policy_version = validation_dict['pi_validate_pipe_vars']['policy']['version']
        project_name = validation_dict['pi_global_vars']['project_name']
    except KeyError:
        validation_results.append(
            {
                'pre-validation': {
                    'errors': f'Invalid key in run_vars. Dumping... {validation_dict}'
                }
            }
        )
        return validation_results

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = git.Repo.clone_from(
                validation_repo,
                temp_dir,
                branch='master'
            )

            if not os.path.isdir(f'{repo.working_tree_dir}/{project_name}'):
                validation_results.append(
                    {
                        'repo': {
                            'errors': f'No project named {project_name}'
                                      f'in {validation_repo}'
                        }
                    }
                )
                return validation_results
            elif not os.path.isdir(
                    f'{repo.working_tree_dir}/{project_name}/releases/{policy_version}'
            ):
                validation_results.append(
                    {
                        'repo': {
                            'errors': f'No release {policy_version}'
                                      f'found in {validation_repo}'
                        }
                    }
                )
                return validation_results

            module_directory = f'{repo.working_tree_dir}/{project_name}/' \
                               f'releases/{policy_version}/pipes/'

            for key, value in validation_dict.items():
                if key in {
                    key
                    for dict in config_keys
                    for key in dict.keys()
                } and key != 'ci':
                    temp_dict = {key: value}
                    [module_name] = [
                        config_key[key]
                        for config_key in config_keys
                        if key in config_key.keys()
                    ]
                    loader = importlib.machinery.SourceFileLoader(
                        module_name[1],
                        f'{module_directory}/{module_name[0]}/{module_name[1]}.py'
                    )
                    spec = importlib.util.spec_from_loader(loader.name, loader)
                    module = importlib.util.module_from_spec(spec)
                    loader.exec_module(module)
                    result = module.validate(temp_dict)
                    if isinstance(result, Exception):
                        validation_results.append(
                            {
                                key: {
                                    'errors': str(result.messages)
                                }
                            }
                        )
                    else:
                        validation_results.append(
                            {
                                key: {
                                    'errors': False
                                }
                            }
                        )
                if key == 'ci':
                    ci_result = False
                    ci_results = []
                    for ci_key, ci_value in value['ci_provider_config'].items():
                        if ci_key == 'stages':
                            loader = importlib.machinery.SourceFileLoader(
                                'pi_gitlab_ci',
                                f'{module_directory}/pi_gitlab_ci/pi_gitlab_ci.py'
                            )
                            spec = importlib.util.spec_from_loader(loader.name, loader)
                            module = importlib.util.module_from_spec(spec)
                            loader.exec_module(module)
                            result = module.validate(
                                ci_key.capitalize(),
                                {'stages': ci_value}
                            )
                            if isinstance(result, Exception):
                                ci_results.append(
                                    {
                                        ci_key: {
                                            'errors': str(result.messages)
                                        }
                                    }
                                )
                            else:
                                ci_results.append(
                                    {
                                        ci_key: {
                                            'errors': False
                                        }
                                    }
                                )
                        elif ci_key == 'include':
                            temp_dict = {ci_key: ci_value}
                            loader = importlib.machinery.SourceFileLoader(
                                'pi_gitlab_ci',
                                f'{module_directory}/pi_gitlab_ci/pi_gitlab_ci.py'
                            )
                            spec = importlib.util.spec_from_loader(loader.name, loader)
                            module = importlib.util.module_from_spec(spec)
                            loader.exec_module(module)
                            result = module.validate(ci_key.capitalize(), temp_dict)
                            if isinstance(result, Exception):
                                ci_results.append(
                                    {
                                        ci_key: {
                                            'errors': str(result.messages)
                                        }
                                    }
                                )
                            else:
                                ci_results.append(
                                    {
                                        ci_key: {
                                            'errors': False
                                        }
                                    }
                                )

                    for item in ci_results:
                        for value in item.values():
                            if not value['errors']:
                                ci_result = {'errors': False}
                            else:
                                ci_result = {'errors': ci_results}

                    validation_results.append({key: ci_result})

            return validation_results

    except Exception as e:
        validation_results.append(
            {
                'error': {
                    'errors': str(e)
                }
            }
        )
        return validation_results
