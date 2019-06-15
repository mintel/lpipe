import logging

import pytest
import boto3
import hashlib
import functools
from botocore.exceptions import ClientError

from lpipe import utils
from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, QueueType, process_event
from tests import fixtures


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "kinesis", "mock_lambda")
class TestMockLambda:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_lambda_fixtures(
        self, invoke_lambda, kinesis_payload, fixture_name, fixture
    ):
        logger = ServerlessLogger(level=logging.DEBUG, process="shepherd")
        logger.persist = True
        response, body = invoke_lambda(
            name="my_lambda", payload=kinesis_payload(fixture["payload"])
        )
        utils.emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert fixture["response"]["stats"] == body["stats"]
