import base64
import json
import warnings
from pathlib import Path

import boto3
import pytest
import pytest_localstack
from decouple import config

from tests import fixtures


localstack = pytest_localstack.patch_fixture(
    services=["kinesis", "lambda"], scope="module", autouse=False, localstack_version="0.9.4"
)


@pytest.fixture(scope="class")
def kinesis_streams():
    return ["TEST_KINESIS_STREAM"]


@pytest.fixture(scope="class")
def environment(kinesis_streams):
    def env(**kwargs):
        vars = {"SENTRY_DSN": "https://public:private@sentry.localhost:1234/1"}
        vars.update(fixtures.ENV)
        for s in kinesis_streams:
            vars[s] = s
        for k, v in kwargs.items():
            vars[k] = v
        return vars

    return env


@pytest.fixture(scope="class")
def kinesis(kinesis_streams):
    client = boto3.client("kinesis")
    try:
        for stream_name in kinesis_streams:
            client.create_stream(StreamName=stream_name, ShardCount=1)
            client.get_waiter("stream_exists").wait(
                StreamName=stream_name, WaiterConfig={"Delay": 2, "MaxAttempts": 2}
            )
        yield kinesis_streams
    finally:
        for stream_name in kinesis_streams:
            client.delete_stream(StreamName=stream_name)
            client.get_waiter("stream_not_exists").wait(
                StreamName=stream_name, WaiterConfig={"Delay": 2, "MaxAttempts": 2}
            )


@pytest.fixture(scope="class")
def mock_lambda(environment):
    lambda_client = boto3.client("lambda")
    with open(str(Path().absolute() / "dummy_lambda/dist/build.zip"), "rb") as f:
        zipped_code = f.read()
        lambda_client.create_function(
            FunctionName="my_lambda",
            Runtime="python3.6",
            Role="foobar",
            Handler="main.lambda_handler",
            Code=dict(ZipFile=zipped_code),
            Timeout=300,
            Environment={"Variables": environment(MOCK_AWS="true")},
        )


@pytest.fixture
def invoke_lambda():
    def inv(name, payload):
        client = boto3.client("lambda")
        response = client.invoke(
            FunctionName=name,
            InvocationType="RequestResponse",
            LogType="Tail",
            Payload=json.dumps(payload).encode(),
        )
        body = response["Payload"].read()
        try:
            body = json.loads(body)
        except:
            pass
        print(response)
        print(body)
        return response, body

    return inv


@pytest.fixture
def kinesis_payload():
    def kin(payloads):
        def fmt(p):
            return {
                "kinesis": {
                    "data": str(base64.b64encode(json.dumps(p).encode()), "utf-8")
                }
            }

        records = [fmt(p) for p in payloads]
        return {"Records": records}

    return kin


@pytest.fixture
def sqs_payload():
    def sqs(payloads):
        return payloads

    return sqs
