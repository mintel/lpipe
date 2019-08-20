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

    def __repr__(self):
        return f"{self.value}"

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if not new_value and not (isinstance(new_value, int) and self.type == bool):
            self._value = None
            return
        elif isinstance(self.type, type) and isinstance(new_value, self.type):
            self._value = new_value
            return

        formatters = {
            str: self._to_str,
            "json": self._to_json,
            int: self._to_int,
            bool: self._to_bool,
            list: self._to_list,
            datetime: self._to_datetime,
        }

        self._value = formatters[self.type](new_value)

    def _to_str(self, v):
        return str(v)

    def _to_json(self, v):
        if isinstance(v, str):
            return json.loads(v)
        elif isinstance(v, dict):
            return v
        else:
            raise ValueError('Could not convert "%s" to JSON.', v)

    def _to_int(self, v):
        if self._represents_int(v):
            return int(v)

    def _to_bool(self, v):
        if isinstance(v, int) or self._represents_int(v):
            if int(v) == 1:
                return True
            elif int(v) == 0:
                return False
            else:
                raise ValueError(
                    'Could not convert "%s" to bool because it did not represent a bool.',
                    v,
                )
        if isinstance(v, str):
            if v.lower() == "true":
                return True
            elif v.lower() == "false":
                return False
            else:
                raise ValueError(
                    'Could not convert "%s" to bool because it did not represent a bool.',
                    v,
                )
        else:
            raise ValueError('Could not convert "%s" to bool.', v)

    def _to_list(self, v):
        if isinstance(v, str):
            return v.split(",")
        else:
            raise ValueError('Could not convert "%s" to list.', v)

    def _to_datetime(self, v):
        if type(v) is datetime:
            return v
        elif isinstance(v, str):
            return dateutil.parser.parse(v)  # expects ISO datetime format
        else:
            raise ValueError('Could not convert "%s" to datetime.', v)

    @staticmethod
    def _represents_int(v):
        try:
            int(v)
            return True
        except ValueError:
            return False


class InvalidPayload(Exception):
    pass
