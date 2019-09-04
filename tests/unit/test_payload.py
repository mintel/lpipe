import json
from datetime import datetime

import pytest

from lpipe.payload import validate_payload, InvalidPayload, Param

from tests.unit import fixtures


class TestParam:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.PARAM_DATA.items()]
    )
    def test_param(self, fixture_name, fixture):
        p = Param(**fixture["param"])
        p.value = fixture["val_in"]
        print(p.value)
        assert p.value == fixture["val_out"]

    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.PARAM_DATA_INVALID.items()]
    )
    def test_param_invalid(self, fixture_name, fixture):
        p = Param(**fixture["param"])
        with pytest.raises(ValueError):
            p.value = fixture["val_in"]
            print(p.value)


class TestValidatePayload:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.PAYLOAD_DATA.items()]
    )
    def test_payload(self, fixture_name, fixture):
        params = validate_payload(fixture["payload"], fixture["schema"])
        print(params)
        assert params == fixture["params_out"]

    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [(k, v) for k, v in fixtures.PAYLOAD_INVALID_DATA.items()],
    )
    def test_payload_invalid(self, fixture_name, fixture):
        with pytest.raises(InvalidPayload):
            payload = validate_payload(fixture["payload"], fixture["schema"])
            print(payload)
