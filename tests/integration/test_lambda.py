import logging

import pytest
from tests import fixtures

from lpipe import utils
from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, QueueType, process_event
from lpipe.testing import invoke_lambda, sqs_payload


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "sqs", "kinesis", "lam")
class TestMockLambda:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_lambda_fixtures(self, fixture_name, fixture):
        logger = ServerlessLogger(level=logging.DEBUG, process="my_lambda")
        logger.persist = True
        response, body = invoke_lambda(
            name="my_lambda", payload=sqs_payload(fixture["payload"])
        )
        utils.emit_logs(body)
        assert utils.check_status(response, keys=["StatusCode"])
        assert fixture["response"]["stats"] == body["stats"]
        if "output" in fixture["response"]:
            assert fixture["response"]["output"] == body["output"]
