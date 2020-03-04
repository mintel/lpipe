import logging

import pytest
from tests import fixtures

from lpipe import sqs, utils
from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, Queue, QueueType, process_event, put_record
from lpipe.testing import kinesis_payload, raw_payload, sqs_payload


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "kinesis", "sqs")
class TestPutRecord:
    def test_kinesis(self, kinesis_streams, set_environment):
        queue = Queue(type=QueueType.KINESIS, path="FOO", name=kinesis_streams[0])
        fixture = {"path": queue.path, "kwargs": {}}
        put_record(queue=queue, record=fixture)

    def test_sqs_by_url(self, sqs_queues, set_environment):
        queue_url = sqs.get_queue_url(sqs_queues[0])
        queue = Queue(type=QueueType.SQS, path="FOO", url=queue_url)
        fixture = {"path": queue.path, "kwargs": {}}
        put_record(queue=queue, record=fixture)

    def test_sqs_by_name(self, sqs_queues, set_environment):
        queue_name = sqs_queues[0]
        queue = Queue(type=QueueType.SQS, path="FOO", name=queue_name)
        fixture = {"path": queue.path, "kwargs": {}}
        put_record(queue=queue, record=fixture)


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "kinesis", "sqs")
class TestProcessEvents:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_fixtures_raw(self, set_environment, fixture_name, fixture):
        logger = ServerlessLogger(level=logging.DEBUG, process="my_lambda")
        logger.persist = True
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=raw_payload(fixture["payload"]),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.RAW,
            logger=logger,
        )
        utils.emit_logs(response)
        assert fixture["response"]["stats"] == response["stats"]
        if "output" in fixture["response"]:
            assert fixture["response"]["output"] == response["output"]

    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_fixtures_kinesis(
        self, set_environment, fixture_name, fixture
    ):
        logger = ServerlessLogger(level=logging.DEBUG, process="my_lambda")
        logger.persist = True
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=kinesis_payload(fixture["payload"]),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.KINESIS,
            logger=logger,
        )
        utils.emit_logs(response)
        assert fixture["response"]["stats"] == response["stats"]
        if "output" in fixture["response"]:
            assert fixture["response"]["output"] == response["output"]

    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_fixtures_sqs(self, set_environment, fixture_name, fixture):
        logger = ServerlessLogger(level=logging.DEBUG, process="my_lambda")
        logger.persist = True
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=sqs_payload(fixture["payload"]),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.SQS,
            logger=logger,
        )
        utils.emit_logs(response)
        assert fixture["response"]["stats"] == response["stats"]
        if "output" in fixture["response"]:
            assert fixture["response"]["output"] == response["output"]

    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            (
                "TEST_FUNC",
                {
                    "payload": [{"foo": "bar"}],
                    "response": {"stats": {"received": 1, "successes": 1}},
                },
            ),
            (
                "TEST_FUNC_MANY",
                {
                    "payload": [{"foo": "bar"}, {"foo": "bar"}, {"foo": "bar"}],
                    "response": {"stats": {"received": 3, "successes": 3}},
                },
            ),
        ],
    )
    def test_process_event_default_path(self, set_environment, fixture_name, fixture):
        logger = ServerlessLogger(level=logging.DEBUG, process="my_lambda")
        logger.persist = True
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=sqs_payload(fixture["payload"]),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.SQS,
            logger=logger,
            default_path="TEST_FUNC",
        )
        utils.emit_logs(response)
        assert fixture["response"]["stats"] == response["stats"]
        if "output" in fixture["response"]:
            assert fixture["response"]["output"] == response["output"]
