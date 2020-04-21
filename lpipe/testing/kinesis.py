"""
Example Usage

```python
@pytest.fixture(scope="session")
def kinesis_streams():
    return ["TEST_KINESIS_STREAM"]

@pytest.fixture(scope="class")
def kinesis(localstack, kinesis_streams):
    with lpipe.testing.setup_kinesis(kinesis_streams) as streams:
        yield streams
```
"""

import base64
import json
from contextlib import contextmanager

import backoff
from botocore.exceptions import ClientError

from .. import _boto3, utils


def kinesis_payload(payloads):
    def fmt(p):
        return {
            "kinesis": {"data": str(base64.b64encode(json.dumps(p).encode()), "utf-8")}
        }

    records = [fmt(p) for p in payloads]
    return {"Records": records}


@backoff.on_exception(backoff.expo, ClientError, max_time=30)
def create_kinesis_stream(
    name: str, waiter_config: dict = {"Delay": 2, "MaxAttempts": 2}
):
    client = _boto3.client("kinesis")
    resp = utils.call(client.create_stream, StreamName=name, ShardCount=1)
    client.get_waiter("stream_exists").wait(StreamName=name, WaiterConfig=waiter_config)
    return resp


def create_kinesis_streams(names: list):
    return {n: create_kinesis_stream(n) for n in names}


@backoff.on_exception(backoff.expo, ClientError, max_time=30)
def destroy_kinesis_stream(
    name: str, waiter_config: dict = {"Delay": 2, "MaxAttempts": 2}
):
    client = _boto3.client("kinesis")
    resp = utils.call(client.delete_stream, StreamName=name)
    client.get_waiter("stream_not_exists").wait(
        StreamName=name, WaiterConfig=waiter_config
    )
    return resp


def destroy_kinesis_streams(names: list):
    return {n: destroy_kinesis_stream(n) for n in names}


@contextmanager
def setup_kinesis(names):
    try:
        yield create_kinesis_streams(names)
    finally:
        destroy_kinesis_streams(names)
