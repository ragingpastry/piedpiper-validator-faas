import git
import os
import tempfile
import zipfile


def build_temp_zipfiles(request):
    zip_files = []
    for zip_file in request.files.getlist("files"):
        temp_directory = tempfile.TemporaryDirectory()
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(zip_file.read())
        tmp_file.flush()
        zip_files.append((tmp_file.name, temp_directory))
    return zip_files


def unzip_files(zip_file, temp_directory):
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(temp_directory)
    zip_ref.close()


def build_run_vars(request):
    receive_zip_files = build_temp_zipfiles(request)
    for zip_file, temp_directory in receive_zip_files:
        unzip_files(zip_file, temp_directory.name)
        for root, dirs, files in os.walk(temp_directory.name):
            for file in files:
                with open(os.path.join(root, file)) as runvars:
                    yield runvars.read()


def clone_repository(remote, destination, branch='master'):
    repo = git.Repo.clone_from(
        remote,
        destination,
        branch=branch
    )
    return repo

