import json
import logging
import warnings

import pytest
import pytest_localstack
from moto import mock_sqs
from tests import fixtures

import lpipe

logger = logging.getLogger()
localstack = pytest_localstack.patch_fixture(
    services=["dynamodb", "kinesis", "sqs", "lambda"],
    scope="class",
    autouse=False,
    region_name=fixtures.ENV["AWS_DEFAULT_REGION"],
)


@pytest.fixture(scope="session")
def kinesis_streams():
    return ["TEST_KINESIS_STREAM"]


@pytest.fixture(scope="class")
def kinesis(localstack, kinesis_streams):
    try:
        yield lpipe.testing.create_kinesis_streams(kinesis_streams)
    finally:
        lpipe.testing.destroy_kinesis_streams(kinesis_streams)


@pytest.fixture(scope="session")
def sqs_queues():
    return ["TEST_SQS_QUEUE"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    try:
        yield lpipe.testing.create_sqs_queues(sqs_queues)
    finally:
        lpipe.testing.destroy_sqs_queues(sqs_queues)


@pytest.fixture(scope="function")
def sqs_moto(sqs_queues, set_environment):
    with mock_sqs():
        try:
            warnings.simplefilter("ignore")
            yield lpipe.testing.create_sqs_queues(sqs_queues)
        finally:
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
    try:
        yield lpipe.testing.create_dynamodb_tables(dynamodb_tables)
    finally:
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
    try:
        yield lpipe.testing.create_lambda(
            path="dummy_lambda/dist/build.zip",
            runtime="python3.6",
            environment=environment(MOCK_AWS=True),
        )
    finally:
        lpipe.testing.destroy_lambda()
