import git
from collections import abc
import zipfile
import requests
import json
from minio import Minio
from .config import Config
import importlib

gman_url = Config.get("gman").get("url")


def read_secrets():
    secrets = {}
    with open("/var/openfaas/secrets/storage-access-key") as access_key:
        secrets.update({"access_key": access_key.read().strip("\n")})
    with open("/var/openfaas/secrets/storage-secret-key") as secret_key:
        secrets.update({"secret_key": secret_key.read().strip("\n")})

    return secrets


def upload_artifact(bucket_name, object_name, file_path, url, access_key, secret_key):
    minioClient = Minio(url, access_key=access_key, secret_key=secret_key, secure=False)

    minioClient.fput_object(bucket_name, object_name, file_path)
    return minioClient.stat_object(bucket_name, object_name)


def download_artifact(bucket_name, object_name, file_path, url, access_key, secret_key):
    minioClient = Minio(url, access_key=access_key, secret_key=secret_key, secure=False)
    return minioClient.fget_object(bucket_name, object_name, file_path)


def unzip_files(zip_file, directory):
    zip_ref = zipfile.ZipFile(zip_file, "r")
    zip_ref.extractall(directory)
    zip_ref.close()


def build_run_vars(file, directory):
    unzip_files(file, directory)
    try:
        with open(f"{directory}/run_vars.yml") as runvars:
            return runvars.read()
    except FileNotFoundError as e:
        return f"File not found. {e}"


def clone_repository(remote, destination, branch="master"):
    repo = git.Repo.clone_from(remote, destination, branch=branch)
    return repo


def query_gman_for_task(task_id):
    r = requests.get(f"{gman_url}/gman/{task_id}")
    r.raise_for_status()
    return r.json()


def update_task_id_status(
    gman_url=None, task_id=None, status=None, message=None, caller=None
):
    try:
        data = {"message": message, "status": status, "caller": caller}
        r = requests.put(f"{gman_url}/gman/{task_id}", data=json.dumps(data))
    except requests.exceptions.RequestException as e:
        message = f"Failed to request new taskID from gman at {gman_url}. \n\n{e}"
        raise

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        message = f"Failed to request new taskID from gman at {gman_url}. \n\n{e}"
        raise
    else:
        id = r.json()["task"]["task_id"]
        return id


def nested_dict_iter(nested):
    for key, value in nested.items():
        if isinstance(value, abc.Mapping):
            yield from nested_dict_iter(value)
        else:
            yield key, value


def load_module_from_file(module_name, file):
    loader = importlib.machinery.SourceFileLoader(module_name, file)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
