import requests
import json


def call_validation_function(run_id=None,
                             faas_url=None,
                             project=None,
                             caller='validator_func',
                             task_id=None,
                             ):

    data = {
        'run_id': run_id,
        'task_id': task_id,
        'project': project,
        'caller': caller,
    }

    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.post(faas_url, data=json.dumps(data), headers=headers)

    return r


def request_new_task_id(run_id=None,
                        gman_url=None,
                        project=None,
                        status='started',
                        caller='validator_func',):
    try:
        (f'Requesting new taskID from gman at {gman_url}')
        data = {
            'run_id': run_id,
            'caller': caller,
            'project': project,
            'message': 'Init validator_function',
            'status': status,
        }
        r = requests.post(f"{gman_url}/gman", data=json.dumps(data))
    except requests.exceptions.RequestException as e:
        message = f"Failed to request new taskID from gman at {gman_url}. \n\n{e}"
        raise

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        message = f"Failed to request new taskID from gman at {gman_url}. \n\n{e}"
        raise
    else:
        id = r.json()['task']['task_id']
        return id
