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
@pytest.mark.usefixtures("localstack", "kinesis")
class TestProcessEvents:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_fixtures(
        self, kinesis_payload, environment, fixture_name, fixture
    ):
        with utils.set_env(environment()):
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
