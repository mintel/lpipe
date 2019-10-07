import base64
import json
import logging
import warnings
from pathlib import Path
from time import sleep

import backoff
import boto3
import pytest
import pytest_localstack
from botocore.exceptions import ClientError
from decouple import config
from pytest_localstack.service_checks import SERVICE_CHECKS

import lpipe
from tests import fixtures

logger = logging.getLogger()

localstack = pytest_localstack.patch_fixture(
    services=["kinesis", "sqs", "lambda"], scope="class", autouse=False
)


def check_status(response, code=2, keys=["ResponseMetadata", "HTTPStatusCode"]):
    status = lpipe.utils.get_nested(response, keys)
    assert status // 100 == code
    return status


@backoff.on_exception(
    backoff.expo, pytest_localstack.exceptions.TimeoutError, max_tries=3
)
def check(session, service):
    return SERVICE_CHECKS[service](session)


@pytest.fixture(scope="session")
def kinesis_streams():
    return ["TEST_KINESIS_STREAM"]


@pytest.fixture(scope="class")
def kinesis(localstack, kinesis_streams):
    check(localstack, "kinesis")
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


@pytest.fixture(scope="session")
def sqs_queues():
    return ["TEST_SQS_QUEUE"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    check(localstack, "sqs")
    client = boto3.client("sqs")

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def create_queue(q):
        response = client.create_queue(QueueName=queue_name)
        check_status(response)
        return response["QueueUrl"]

    def queue_exists(q):
        try:
            lpipe.sqs.get_queue_url(q)
            return True
        except:
            return False

    try:
        queues = {}

        for queue_name in sqs_queues:
            try:
                queues[queue_name] = create_queue(queue_name)
            except ClientError:
                exists = queue_exists(queue_name)
                raise Exception(f"queue_exists({queue_name}) -> {exists}") from e

        for queue_name in sqs_queues:
            while not queue_exists(queue_name):
                sleep(1)

        yield queues
    finally:
        for queue_name in sqs_queues:
            client.delete_queue(QueueUrl=lpipe.sqs.get_queue_url(queue_name))


@pytest.fixture(scope="class")
def environment(sqs_queues, kinesis_streams):
    def env(**kwargs):
        vars = {
            "APP_ENVIRONMENT": "localstack",
            "SENTRY_DSN": "https://public:private@sentry.localhost:1234/1",
        }
        vars.update(fixtures.ENV)
        for name in kinesis_streams:
            vars[name] = name
        for name in sqs_queues:
            vars[name] = name
        for k, v in kwargs.items():
            vars[k] = v
        return vars

    return env


@pytest.fixture(scope="class")
def lam(localstack, environment):
    name = "my_lambda"
    runtime = "python3.6"
    role = "foobar"
    handler = "main.lambda_handler"
    path = "dummy_lambda/dist/build.zip"

    def clean_env(env):
        for k, v in env.items():
            if isinstance(v, bool):
                if v:
                    env[k] = str(v)
                else:
                    continue
            elif isinstance(v, type(None)):
                env[k] = ""
        return env

    try:
        lam = boto3.client("lambda")
        with open(str(Path().absolute() / path), "rb") as f:
            zipped_code = f.read()
            lam.create_function(
                FunctionName=name,
                Runtime=runtime,
                Role=role,
                Handler=handler,
                Code=dict(ZipFile=zipped_code),
                Timeout=300,
                Environment={"Variables": clean_env(environment(MOCK_AWS=True))},
            )
        yield
    finally:
        lam.delete_function(FunctionName=name)


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
        body = response["Payload"].read().decode("utf-8")
        try:
            body = json.loads(body)
        except:
            pass
        return response, body

    return inv


@pytest.fixture
def raw_payload():
    def raw(payloads):
        def fmt(p):
            return json.dumps(p).encode()

        records = [fmt(p) for p in payloads]
        return records

    return raw


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
        def fmt(p):
            return {"body": json.dumps(p).encode()}

        records = [fmt(p) for p in payloads]
        return {"Records": records}

    return sqs
