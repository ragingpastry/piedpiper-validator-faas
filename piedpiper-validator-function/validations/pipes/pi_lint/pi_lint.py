from marshmallow import fields
from marshmallow import Schema
from marshmallow import RAISE
from marshmallow import ValidationError
from marshmallow import validates


class LintPipeVars(Schema):
    run_pipe = fields.Bool(required=True)
    url = fields.Str(required=True)

    @validates('run_pipe')
    def validate_run_pipe(self, value):
        defined_value = True
        if value != defined_value:
            raise ValidationError(f'Lint Pipe must be enabled. You supplied {value}')

    @validates('url')
    def validate_url(self, value):
        defined_value = 'http://172.17.0.1:8080/function'
        if value != defined_value:
            raise ValidationError(f'Lint pipe URL must be {defined_value} ')


class LintPipeConfig(Schema):
    pi_lint_pipe_vars = fields.Nested(LintPipeVars)


def validate(config):
    schema = LintPipeConfig(unknown=RAISE)
    try:
       _ = schema.load(config)
       result = True
    except ValidationError as err:
        result = err
    return result
