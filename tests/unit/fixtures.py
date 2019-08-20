import json
from datetime import datetime

from api.payload import Param

NOW = datetime.now()

PARAM_DATA = {
    "str": {"param": {"type": str}, "val_in": "foo", "val_out": "foo"},
    "json": {
        "param": {"type": "json"},
        "val_in": json.dumps({"foo": "bar"}),
        "val_out": {"foo": "bar"},
    },
    "int_from_str": {"param": {"type": int}, "val_in": "1234", "val_out": 1234},
    "bool_from_int": {"param": {"type": bool}, "val_in": 1, "val_out": True},
    "bool_from_int_false": {"param": {"type": bool}, "val_in": 0, "val_out": False},
    "bool_from_int_as_str": {"param": {"type": bool}, "val_in": "1", "val_out": True},
    "bool_from_int_as_str_false": {
        "param": {"type": bool},
        "val_in": "0",
        "val_out": False,
    },
    "bool_from_str": {"param": {"type": bool}, "val_in": "TRUE", "val_out": True},
    "bool_from_str_false": {
        "param": {"type": bool},
        "val_in": "FALSE",
        "val_out": False,
    },
    "list_one": {"param": {"type": list}, "val_in": "1", "val_out": ["1"]},
    "list_many": {
        "param": {"type": list},
        "val_in": "1,2,3",
        "val_out": ["1", "2", "3"],
    },
    "datetime": {"param": {"type": datetime}, "val_in": NOW, "val_out": NOW},
    "datetime_from_str": {
        "param": {"type": datetime},
        "val_in": NOW.isoformat(),
        "val_out": NOW,
    },
    "default_is_not_required": {
        "param": {"type": str, "default": "wiz"},
        "val_in": None,
        "val_out": "wiz",
    },
    "not_required_is_not_required": {
        "param": {"type": str, "required": False},
        "val_in": None,
        "val_out": None,
    },
}

PARAM_DATA_INVALID = {
    "json": {"param": {"type": "json"}, "val_in": "foo"},
    "bool_from_str": {"param": {"type": bool}, "val_in": "truee"},
    "bool_from_str_false": {"param": {"type": bool}, "val_in": "falsee"},
    "bool_from_int": {"param": {"type": bool}, "val_in": 1234},
    "required_is_required": {"param": {"type": str, "required": True}, "val_in": None},
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
    "str_unset_default": {
        "payload": {},
        "schema": {"foo": Param(str, default="wiz", required=False)},
        "params_out": {"foo": "wiz"},
    },
}

PAYLOAD_INVALID_DATA = {
    "str": {"payload": {}, "schema": {"foo": Param(str)}},
    "str_unset_default": {"payload": {}, "schema": {"foo": Param(str, default="wiz")}},
}
