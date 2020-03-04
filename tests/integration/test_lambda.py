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
        payload = sqs_payload(fixture["payload"])
        response, body = invoke_lambda(name="my_lambda", payload=payload)
        for k, v in fixture["response"].items():
            assert body[k] == v
