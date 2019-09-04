import json
from datetime import datetime

from lpipe.payload import Param

NOW = datetime.now()

PARAM_DATA = {
    "str": {"param": {"type": str}, "val_in": "foo", "val_out": "foo"},
    "str_from_none": {"param": {"type": str}, "val_in": None, "val_out": None},
    "int": {"param": {"type": int}, "val_in": 1234, "val_out": 1234},
    "int_from_none": {"param": {"type": int}, "val_in": None, "val_out": None},
    "bool": {"param": {"type": bool}, "val_in": True, "val_out": True},
    "bool_from_none": {"param": {"type": bool}, "val_in": None, "val_out": None},
    "list_one": {"param": {"type": list}, "val_in": [1], "val_out": [1]},
    "list_many": {
        "param": {"type": list},
        "val_in": [1,2,3],
        "val_out": [1, 2, 3],
    },
    "list_from_none": {"param": {"type": list}, "val_in": None, "val_out": None},
    "datetime": {"param": {"type": datetime}, "val_in": NOW, "val_out": NOW},
    "datetime_from_none": {
        "param": {"type": datetime},
        "val_in": None,
        "val_out": None,
    },
}

PARAM_DATA_INVALID = {
    "str_from_int": {"param": {"type": str}, "val_in": 1},
}

PAYLOAD_DATA = {
    "str_required": {
        "payload": {"foo": "bar"},
        "schema": {"foo": Param(str)},
        "params_out": {"foo": "bar"},
    },
    "str_unset": {
        "payload": {},
        "schema": {"foo": Param(str, required=False)},
        "params_out": {"foo": None},
    },
    "str_unset_default_required": {
        "payload": {},
        "schema": {"foo": Param(str, default="wiz")},
        "params_out": {"foo": "wiz"},
    },
    "str_unset_default": {
        "payload": {},
        "schema": {"foo": Param(str, default="wiz", required=False)},
        "params_out": {"foo": "wiz"},
    },
    "none_sets_none": {
        "payload": {
            "str": None,
            "bool": None,
            "int": None,
            "list": None,
            "datetime": None,
        },
        "schema": {
            "str": Param(str),
            "bool": Param(bool),
            "int": Param(int),
            "list": Param(list),
            "datetime": Param(datetime),
        },
        "params_out": {
            "str": None,
            "bool": None,
            "int": None,
            "list": None,
            "datetime": None,
        },
    },
}

PAYLOAD_INVALID_DATA = {"str": {"payload": {}, "schema": {"foo": Param(str)}}}
