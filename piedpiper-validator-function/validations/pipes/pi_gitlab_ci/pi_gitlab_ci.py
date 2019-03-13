from marshmallow import fields
from marshmallow import Schema
from marshmallow import RAISE
from marshmallow import ValidationError
from marshmallow import validates


class Stages(Schema):
    stages = fields.List(fields.String(), required=True)

    @validates('stages')
    def validate_stages(self, value):
        required_stages = [
            'lint'
        ]
        errors = []
        for stage in required_stages:
            if stage not in value:
                errors.append(ValueError(f'Stages must include {stage}. You passed {value}'))
        if len(errors):
            raise ValidationError(errors)


class IncludeProjects(Schema):
    project = fields.Str(required=True)
    file = fields.Str(required=True)


class Include(Schema):
    include = fields.List(fields.Nested(IncludeProjects), many=True)

    @validates('include')
    def validate_include(self, value):
        errors = []
        required_includes = [
            {'project': 'piedpiper/validation', 'file': '.gitlab-ci.yml'}
        ]
        for include in required_includes:
            if include not in value:
                errors.append(ValueError(f'Includes must include {include}. You passed {value}'))

        if len(errors):
            raise ValidationError(errors)


def validate(schema, config):
    #validation = type(schema, (), {"unknown": RAISE})
    validation_schema = globals()[schema]
    validation = validation_schema(unknown=RAISE)
    try:
        _ = validation.load(config)
        result = True
    except ValidationError as err:
        result = err
    return result
