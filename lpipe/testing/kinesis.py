"""
Example Usage

```python
@pytest.fixture(scope="session")
def kinesis_streams():
    return ["TEST_KINESIS_STREAM"]


@pytest.fixture(scope="class")
def kinesis(localstack, kinesis_streams):
    yield lpipe.testing.create_kinesis_streams(kinesis_streams)
    lpipe.testing.destroy_kinesis_streams(kinesis_streams)
```
"""

import base64
import json

import backoff
import boto3
from botocore.exceptions import ClientError

from .. import utils


def kinesis_payload(payloads):
    def fmt(p):
        return {
            "kinesis": {"data": str(base64.b64encode(json.dumps(p).encode()), "utf-8")}
        }

    records = [fmt(p) for p in payloads]
    return {"Records": records}


@backoff.on_exception(backoff.expo, ClientError, max_time=30)
def create_kinesis_stream(name):
    utils.call(boto3.client("kinesis").create_stream, StreamName=name, ShardCount=1)


def create_kinesis_streams(
    names: list, waiter_config: dict = {"Delay": 2, "MaxAttempts": 2}
):
    client = boto3.client("kinesis")
    for name in names:
        create_kinesis_stream(name)
        client.get_waiter("stream_exists").wait(
            StreamName=name, WaiterConfig=waiter_config
        )


def destroy_kinesis_streams(names: list):
    client = boto3.client("kinesis")
    for name in names:
        utils.call(client.delete_stream, StreamName=name)
        client.get_waiter("stream_not_exists").wait(
            StreamName=name, WaiterConfig={"Delay": 2, "MaxAttempts": 2}
        )
