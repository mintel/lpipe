import json
from datetime import datetime
from urllib.parse import unquote

import dateutil


def validate_payload(payload, schema):
    validated_params = {}
    for param_name, param in schema.items():
        if param.required and not param.value:
            try:
                assert param_name in payload
            except:
                raise InvalidPayload(f"{param_name} is a required parameter.")

        try:
            if param_name in payload:
                param.value = payload[param_name]
        except ValueError:
            raise InvalidPayload(
                f"The value you provided for {param_name} was invalid."
            )

        validated_params[param_name] = param

    return {k: v.value for k, v in validated_params.items()}


class Param:
    """An API request parameter."""

    def __init__(self, type, default=None, required=True):
        self.type = type
        self.value = default
        self.required = required
        assert self.valid

    def __repr__(self):
        return f"{self.value}"

    @property
    def valid(self):
        assert isinstance(self.type, type)
        return True

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if isinstance(new_value, self.type):
            self._value = new_value
            return


class InvalidPayload(Exception):
    pass
