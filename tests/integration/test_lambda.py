import base64
import json
import logging

import pytest
import boto3
import hashlib
import functools
from botocore.exceptions import ClientError

from lpipe import utils
from tests import fixtures


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "kinesis")
class TestProcessEvents:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_fixtures(self, kinesis_payload, fixture_name, fixture):
        with utils.set_env(fixtures.ENV):
            logger = ServerlessLogger(level=logging.DEBUG, process="shepherd")
            logger.persist = True
            from func.main import Path, PATHS

            response = process_event(
                event=kinesis_payload(fixture["payload"]),
                path_enum=Path,
                paths=PATHS,
                queue_type=QueueType.KINESIS,
                logger=logger,
            )
            utils.emit_logs(response)
            assert fixture["response"]["stats"] == response["stats"]


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
        with utils.set_env(fixtures.ENV):
            response, body = invoke_lambda(
                name="my_lambda", payload=kinesis_payload(fixture["payload"])
            )
        utils.emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert fixture["response"]["stats"] == body["stats"]
