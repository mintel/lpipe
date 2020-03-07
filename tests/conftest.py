import json
import logging

import moto
import pytest
import pytest_localstack
from decouple import config
from tests import fixtures

import lpipe

logger = logging.getLogger()
localstack = pytest_localstack.patch_fixture(
    services=["dynamodb", "kinesis", "sqs", "lambda"],
    scope="class",
    autouse=False,
    region_name=fixtures.ENV["AWS_DEFAULT_REGION"],
)


@pytest.fixture(scope="session", autouse=True)
def requests_log_level():
    for name in ("requests", "urllib3"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        logger.propagate = True


@pytest.fixture(scope="session")
def kinesis_streams():
    return ["test-kinesis-stream"]


@pytest.fixture(scope="class")
def kinesis(localstack, kinesis_streams):
    yield lpipe.testing.create_kinesis_streams(kinesis_streams)
    lpipe.testing.destroy_kinesis_streams(kinesis_streams)


@pytest.fixture(scope="class")
def kinesis_moto(kinesis_streams, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_kinesis():
            yield lpipe.testing.create_kinesis_streams(kinesis_streams)
            lpipe.testing.destroy_kinesis_streams(kinesis_streams)


@pytest.fixture(scope="session")
def sqs_queues():
    return ["test-sqs-queue"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    yield lpipe.testing.create_sqs_queues(sqs_queues)
    lpipe.testing.destroy_sqs_queues(sqs_queues)


@pytest.fixture(scope="class")
def sqs_moto(sqs_queues, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_sqs():
            yield lpipe.testing.create_sqs_queues(sqs_queues)
            lpipe.testing.destroy_sqs_queues(sqs_queues)


@pytest.fixture(scope="session")
def dynamodb_tables():
    return [
        {
            "AttributeDefinitions": [
                {"AttributeName": "uri", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            "TableName": "my-dbd-table",
            "KeySchema": [
                {"AttributeName": "uri", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
        }
    ]


@pytest.fixture(scope="class")
def dynamodb(localstack, dynamodb_tables):
    yield lpipe.testing.create_dynamodb_tables(dynamodb_tables)
    lpipe.testing.destroy_dynamodb_tables(dynamodb_tables)


@pytest.fixture(scope="class")
def dynamodb_moto(dynamodb_tables, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_dynamodb2():
            yield lpipe.testing.create_dynamodb_tables(dynamodb_tables)
            lpipe.testing.destroy_dynamodb_tables(dynamodb_tables)


@pytest.fixture(scope="class")
def environment(sqs_queues, kinesis_streams, dynamodb_tables):
    return lpipe.testing.environment(
        fixtures=fixtures.ENV,
        sqs_queues=sqs_queues,
        kinesis_streams=kinesis_streams,
        dynamodb_tables=dynamodb_tables,
    )


@pytest.fixture(scope="function")
def set_environment(environment):
    with lpipe.utils.set_env(environment()):
        yield


@pytest.fixture(scope="class")
def lam(localstack, environment):
    yield lpipe.testing.create_lambda(
        path="dummy_lambda/dist/build.zip",
        runtime="python3.6",
        environment=environment(MOCK_AWS=True),
    )
    lpipe.testing.destroy_lambda()
