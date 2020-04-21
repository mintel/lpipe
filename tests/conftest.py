import logging

import moto
import pytest
import pytest_localstack
from tests import fixtures

import lpipe

logger = logging.getLogger()
localstack = pytest_localstack.patch_fixture(
    services=["dynamodb", "kinesis", "sqs", "s3", "lambda"],
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
    with lpipe.testing.setup_kinesis(kinesis_streams) as streams:
        yield streams


@pytest.fixture(scope="class")
def kinesis_moto(kinesis_streams, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_kinesis():
            with lpipe.testing.setup_kinesis(kinesis_streams) as streams:
                yield streams


@pytest.fixture(scope="session")
def sqs_queues():
    return ["test-sqs-queue"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    with lpipe.testing.setup_sqs(sqs_queues, redrive=True) as queues:
        yield queues


@pytest.fixture(scope="class")
def sqs_moto(sqs_queues, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_sqs():
            with lpipe.testing.setup_sqs(sqs_queues, redrive=True) as queues:
                yield queues


@pytest.fixture(scope="session")
def dynamodb_tables():
    return [
        {
            "AttributeDefinitions": [
                {"AttributeName": "uri", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            "TableName": "test-dbd-table",
            "KeySchema": [
                {"AttributeName": "uri", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
        }
    ]


@pytest.fixture(scope="class")
def dynamodb(localstack, dynamodb_tables):
    with lpipe.testing.setup_dynamodb(dynamodb_tables) as tables:
        yield tables


@pytest.fixture(scope="class")
def dynamodb_moto(dynamodb_tables, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_dynamodb2():
            with lpipe.testing.setup_dynamodb(dynamodb_tables) as tables:
                yield tables


@pytest.fixture(scope="session")
def s3_buckets():
    return ["test-bucket"]


@pytest.fixture(scope="class")
def s3(localstack, s3_buckets):
    with lpipe.testing.setup_s3(s3_buckets) as buckets:
        yield buckets


@pytest.fixture(scope="class")
def s3_moto(s3_buckets, environment):
    with lpipe.utils.set_env(environment()):
        with moto.mock_s3():
            with lpipe.testing.setup_s3(s3_buckets) as buckets:
                yield buckets


@pytest.fixture(scope="class")
def environment(sqs_queues, kinesis_streams, dynamodb_tables, s3_buckets):
    return lpipe.testing.environment(
        fixtures=fixtures.ENV,
        sqs_queues=sqs_queues,
        kinesis_streams=kinesis_streams,
        dynamodb_tables=dynamodb_tables,
        s3_buckets=s3_buckets,
    )


@pytest.fixture(scope="function")
def set_environment(environment):
    with lpipe.utils.set_env(environment()):
        yield


@pytest.fixture(scope="class")
def lam(localstack, environment):
    with lpipe.testing.setup_awslambda(
        path="dummy_lambda/dist/build.zip",
        runtime="python3.6",
        environment=environment(MOCK_AWS=True),
    ) as lam:
        yield lam
