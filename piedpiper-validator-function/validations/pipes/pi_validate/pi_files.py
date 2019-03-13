from marshmallow import fields
from marshmallow import Schema
from marshmallow import RAISE
from marshmallow import ValidationError
from marshmallow import validates


class FileVars(Schema):
    file = fields.Str(required=True)
    linter = fields.Str(required=True)

    @validates('linter')
    def validate_linter(self, value):
        allowed_linters = [
            'noop',
            'cpplint',
            'flake8'
        ]

        errors = []
        if value not in allowed_linters:
            errors.append(ValueError(f'File linter must be one of {allowed_linters}. You passed {value}'))
        if len(errors):
            raise ValidationError(errors)


class FileConfig(Schema):
    file_config = fields.List(fields.Nested(FileVars), many=True)


def validate(config):
    schema = FileConfig(unknown=RAISE)
    try:
       _ = schema.load(config)
       result = True
    except ValidationError as err:
        result = err
    return result
