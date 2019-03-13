import tempfile
import os
import zipfile

from marshmallow import fields
from marshmallow import Schema
from marshmallow import RAISE
from marshmallow import ValidationError
from marshmallow import validates

import marshmallow


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


class PiGlobalVarsSchema(Schema):
    project_name = fields.Str(required=True)
    vars_dir = fields.Str(required=True)
    version = fields.Str(required=True)

    @validates('project_name')
    def validate_project_name(self, value):
        if value != 'cppp_and_python_project':
            raise ValueError('Project name must be cpp_and_python_project')


class BaseSchema(Schema):
    pi_global_vars = fields.Nested(PiGlobalVarsSchema)

def validate(config):
    schema = BaseSchema(unknown=RAISE)
    try:
       _ = schema.load(config)
       result = True
    except ValidationError as err:
        result = err
    return result
