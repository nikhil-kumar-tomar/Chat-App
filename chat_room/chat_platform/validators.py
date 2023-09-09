from django.core.exceptions import ValidationError

def username_validate(value):
    if '_' in value:
        raise ValidationError("Username cannot contain underscores ('_').")
    return value
