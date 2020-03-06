import logging
from copy import deepcopy

import pytest
from decouple import config
from tests import fixtures

from lpipe import sqs, utils
from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, Queue, QueueType, process_event, put_record
from lpipe.testing import (
    MockContext,
    emit_logs,
    kinesis_payload,
    raw_payload,
    sqs_payload,
)


@pytest.mark.postbuild
@pytest.mark.usefixtures("kinesis", "sqs")
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
@pytest.mark.usefixtures("kinesis", "sqs")
class TestProcessEvents:
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_raw(self, set_environment, fixture_name, fixture):
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=raw_payload(fixture["payload"]),
            context=MockContext(function_name=config("FUNCTION_NAME")),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.RAW,
            debug=True,
        )
        emit_logs(response)
        for k, v in fixture["response"].items():
            assert response[k] == v

    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_kinesis(self, set_environment, fixture_name, fixture):
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=kinesis_payload(fixture["payload"]),
            context=MockContext(function_name=config("FUNCTION_NAME")),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.KINESIS,
            debug=True,
        )
        emit_logs(response)
        for k, v in fixture["response"].items():
            assert response[k] == v

    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_sqs(self, set_environment, fixture_name, fixture):
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=sqs_payload(fixture["payload"]),
            context=MockContext(function_name=config("FUNCTION_NAME")),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.SQS,
            debug=True,
        )
        emit_logs(response)
        for k, v in fixture["response"].items():
            assert response[k] == v

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
        from dummy_lambda.func.main import Path, PATHS

        response = process_event(
            event=sqs_payload(fixture["payload"]),
            context=MockContext(function_name=config("FUNCTION_NAME")),
            path_enum=Path,
            paths=PATHS,
            queue_type=QueueType.SQS,
            debug=True,
            default_path="TEST_FUNC",
        )
        emit_logs(response)
        for k, v in fixture["response"].items():
            assert response[k] == v

    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event_autogenerate_path(
        self, set_environment, fixture_name, fixture
    ):
        from dummy_lambda.func.main import PATHS

        # Simulate a PATHS dictionary where the user didn't define and use an enumeration.
        _PATHS = {
            str(path).split(".")[-1]: [a.copy() for a in actions]
            for path, actions in deepcopy(PATHS).items()
        }

        response = process_event(
            event=raw_payload(fixture["payload"]),
            context=MockContext(function_name=config("FUNCTION_NAME")),
            paths=_PATHS,
            queue_type=QueueType.RAW,
            debug=True,
        )
        emit_logs(response)
        for k, v in fixture["response"].items():
            assert response[k] == v
