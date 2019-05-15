import git
import zipfile
import requests
import json
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)
from .config import Config

gman_url = Config.get('gman').get('url')


def upload_artifact(bucket_name, object_name, file_path, url, access_key, secret_key):
    minioClient = Minio(url,
                        access_key=access_key,
                        secret_key=secret_key,
                        secure=False
                        )

    minioClient.fput_object(bucket_name, object_name, file_path)
    return minioClient.stat_object(bucket_name, object_name)


def download_artifact(bucket_name, object_name, file_path, url, access_key, secret_key):
    minioClient = Minio(url,
                        access_key=access_key,
                        secret_key=secret_key,
                        secure=False
                        )
    return minioClient.fget_object(bucket_name, object_name, file_path)


def unzip_files(zip_file, directory):
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(directory)
    zip_ref.close()


def build_run_vars(file, directory):
    unzip_files(file, directory)
    try:
        with open(f'{directory}/run_vars.yml') as runvars:
            return runvars.read()
    except FileNotFoundError as e:
        return f'File not found. {e}'


def clone_repository(remote, destination, branch='master'):
    repo = git.Repo.clone_from(
        remote,
        destination,
        branch=branch
    )
    return repo

def query_gman_for_task(task_id):
    r = requests.get(f'{gman_url}/gman/taskid/{task_id}')
    r.raise_for_status()
    return r.json()


def notify_gman(task_id, status=None):

    notify_data = {
        'task': {
            'task_id': task_id,
            'status': status,
        }
    }

    r = requests.put(f'{gman_url}/gman/taskid/{task_id}', data=json.dumps(notify_data))
    r.raise_for_status()
    return r.json()


def request_new_task_id(run_id=None,
                        gman_url=None,
                        project=None,
                        caller='validator_func',):
    try:
        (f'Requesting new taskID from gman at {gman_url}')
        data = {
            'run_id': run_id,
            'caller': caller,
            'project': project,
            'message': 'Init validator_function',
            'status': 'executing',
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
