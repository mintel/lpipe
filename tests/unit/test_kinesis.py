import pytest

from lpipe.kinesis import build


class TestBuild:
    def test_build(self):
        result = build(record_data={"foo": "bar"})
        assert result["Data"] == '{"foo": "bar"}'
