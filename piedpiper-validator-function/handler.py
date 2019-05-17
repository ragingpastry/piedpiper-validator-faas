import importlib
import tempfile
import os
import git
import yaml
from .util import build_run_vars, update_task_id_status, download_artifact, upload_artifact, read_secrets
from .config import Config

gman_url = Config['gman']['url']
storage_url = Config['storage']['url']

def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """

    artifact_url = request.get_json().get('artifact_url')
    run_id = request.get_json().get('run_id')
    project = request.get_json().get('project')
    task_id = request.get_json()['task_id']
    hash = request.get_json().get('hashsum')

    validation_artifact = {}

    access_key = read_secrets().get('access_key')
    secret_key = read_secrets().get('secret_key')

    update_task_id_status(gman_url=gman_url, status='received', task_id=task_id,
                          message='Received execution task from validator gateway')

    ## Download artifact from artifact URL
    temp_directory = tempfile.TemporaryDirectory()
    download_artifact(run_id, 'artifacts/validation.zip', f'{temp_directory.name}/validation.zip', storage_url, access_key, secret_key)
    ## Process
    ## Upload logs to artman
    ## Tell gman we are done executing
    config_keys = [
        {'pi_style_pipe_vars': ['pi_style', 'pi_style']},
        {'pi_validate_pipe_vars': ['pi_validate', 'pi_validate']},
        {'file_config': ['pi_validate', 'pi_files']},
        {'ci': ['pi_ci_gitlab', 'pi_ci_gitlab']}
    ]

    validation_repo = 'https://github.com/AFCYBER-DREAM/piedpiper-project-validations.git'

    validation_results = []
    validation_dict = yaml.safe_load(
        build_run_vars(
            f'{temp_directory.name}/validation.zip',
            temp_directory.name)
    )
    try:
        policy_version = validation_dict['pi_validate_pipe_vars']['policy']['version']
        project_name = validation_dict['pi_global_vars']['project_name']
    except KeyError as e:
        update_task_id_status(gman_url=gman_url, task_id=task_id, status='failed',
                              message=f'Invalid key in run_vars.\e{e}')
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

    except Exception as e:
        validation_results.append(
            {
                'error': {
                    'errors': str(e)
                }
            }
        )

    finally:
        validation_log_file = f'{temp_directory.name}/validation.log'
        with open(validation_log_file, 'w') as log_file:
            log_file.write(yaml.safe_dump(validation_results))
        upload_artifact(run_id, 'artifacts/validation.log', validation_log_file, storage_url, access_key, secret_key)
        update_task_id_status(gman_url=gman_url, task_id=task_id,
                              status='completed', message='Validator execution complete')
