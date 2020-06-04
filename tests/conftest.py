import logging

import boto3_fixtures as b3f
import moto
import pytest
from tests import fixtures

import lpipe

logger = logging.getLogger()
stack_config = {
    "services": ["sqs", "kinesis"],
    "autouse": False,
    "scope": "class",
    "region_name": fixtures.ENV["AWS_DEFAULT_REGION"],
}
aws = b3f.contrib.pytest.moto_fixture(**stack_config)
sqs = b3f.contrib.pytest.service_fixture("sqs", scope="class", queues=fixtures.SQS)
kinesis = b3f.contrib.pytest.service_fixture(
    "kinesis", scope="class", streams=fixtures.KINESIS
)


@pytest.fixture(scope="session", autouse=True)
def requests_log_level():
    for name in ("requests", "urllib3"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        logger.propagate = True


@pytest.fixture(scope="class")
def environment():
    return b3f.utils.environment(
        fixtures=fixtures.ENV, sqs_queues=fixtures.SQS, kinesis_streams=fixtures.KINESIS
    )


@pytest.fixture(scope="function")
def set_environment(environment):
    with lpipe.utils.set_env(environment()):
        yield
