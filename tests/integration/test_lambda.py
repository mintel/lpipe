import logging

import pytest
from decouple import config
from tests import fixtures

from lpipe import utils
from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, QueueType, process_event
from lpipe.testing import invoke_lambda, sqs_payload


@pytest.mark.postbuild
@pytest.mark.usefixtures("sqs", "kinesis", "lam")
class TestMockLambda:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_lambda_fixtures(self, set_environment, fixture_name, fixture):
        payload = sqs_payload(fixture["payload"])
        response, body = invoke_lambda(name=config("FUNCTION_NAME"), payload=payload)
        for k, v in fixture["response"].items():
            assert body[k] == v
