from copy import deepcopy
from enum import Enum

import boto3_fixtures as b3f
import botocore
import pytest
from decouple import config
from tests import fixtures

from lpipe import exceptions, testing
from lpipe.action import Action
from lpipe.contrib.sqs import get_queue_url
from lpipe.payload import Payload
from lpipe.pipeline import (
    get_event_source,
    get_kinesis_payload,
    get_payload_from_record,
    get_records_from_event,
    get_sqs_payload,
    process_event,
    put_record,
)
from lpipe.queue import Queue, QueueType


def exception_handler(e):
    pass


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("sqs", {"encode_func": testing.sqs_payload, "decode_func": get_sqs_payload}),
        (
            "kinesis",
            {
                "encode_func": testing.kinesis_payload,
                "decode_func": get_kinesis_payload,
            },
        ),
    ],
)
def test_encode_payload(fixture_name, fixture):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = fixture["encode_func"](records)
    assert "Records" in payload
    decoded_records = [fixture["decode_func"](r) for r in payload["Records"]]
    for r in decoded_records:
        assert "path" in r
        assert r["path"] == "foo"
        assert "kwargs" in r
        assert isinstance(r["kwargs"], dict)


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("sqs", {"encode_func": testing.sqs_payload, "queue_type": QueueType.SQS}),
        (
            "kinesis",
            {"encode_func": testing.kinesis_payload, "queue_type": QueueType.KINESIS},
        ),
        ("raw", {"encode_func": testing.raw_payload, "queue_type": QueueType.RAW}),
    ],
)
def test_get_records_from_event(fixture_name, fixture):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = fixture["encode_func"](records)
    event_records = get_records_from_event(fixture["queue_type"], payload)
    assert len(records) == len(event_records)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_get_event_source_invalid():
    # with pytest.raises(UserWarning):
    assert get_event_source(None, {}) is None


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("sqs", {"encode_func": testing.sqs_payload, "queue_type": QueueType.SQS}),
        (
            "kinesis",
            {"encode_func": testing.kinesis_payload, "queue_type": QueueType.KINESIS},
        ),
        ("raw", {"encode_func": testing.raw_payload, "queue_type": QueueType.RAW}),
    ],
)
def test_get_payload_from_record(fixture_name, fixture):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = fixture["encode_func"](records)
    event_records = get_records_from_event(fixture["queue_type"], payload)
    payload_records = [
        get_payload_from_record(fixture["queue_type"], r) for r in event_records
    ]
    assert payload_records == records


def test_get_payload_from_record_invalid():
    with pytest.raises(exceptions.InvalidPayloadError):
        get_payload_from_record(QueueType.RAW, "badjsonstring")


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [("name", {"name": "foobar"}), ("url", {"url": "http://www.foo.com/bar"})],
)
def test_queue(fixture_name, fixture):
    q = Queue(QueueType.SQS, "FOO", **fixture)
    assert q


class Path(Enum):
    FOO = 1


class TestPayload:
    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            ("enum", {"path": Path.FOO, "kwargs": {"foo": "bar"}}),
            ("string", {"path": "FOO", "kwargs": {"foo": "bar"}}),
            ("empty_kwargs", {"path": Path.FOO, "kwargs": {}}),
        ],
    )
    def test_payload(self, fixture_name, fixture):
        Payload(**fixture).validate(Path)

    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            ("enum", {"type": QueueType.SQS, "path": Path.FOO, "name": "foobar"}),
            ("string", {"type": QueueType.SQS, "path": "FOO", "name": "foobar"}),
        ],
    )
    def test_queue_payload(self, fixture_name, fixture):
        q = Queue(**fixture)
        Payload(queue=q, kwargs={"foo": "bar"}).validate()


@pytest.mark.usefixtures("sqs", "kinesis")
class TestPutRecord:
    def test_kinesis(self, set_environment):
        kinesis_streams = fixtures.KINESIS
        queue = Queue(type=QueueType.KINESIS, path="FOO", name=kinesis_streams[0])
        fixture = {"path": queue.path, "kwargs": {}}
        put_record(queue=queue, record=fixture)

    def test_sqs_by_url(self, set_environment):
        sqs_queues = fixtures.SQS
        queue_url = get_queue_url(sqs_queues[0])
        queue = Queue(type=QueueType.SQS, path="FOO", url=queue_url)
        fixture = {"path": queue.path, "kwargs": {}}
        put_record(queue=queue, record=fixture)

    def test_sqs_by_name(self, set_environment):
        sqs_queues = fixtures.SQS
        queue_name = sqs_queues[0]
        queue = Queue(type=QueueType.SQS, path="FOO", name=queue_name)
        fixture = {"path": queue.path, "kwargs": {}}
        put_record(queue=queue, record=fixture)

    def test_sqs_fail_to_discover_url(self, set_environment):
        queue = Queue(type=QueueType.SQS, path="FOO", name="badqueue")
        fixture = {"path": queue.path, "kwargs": {}}
        with pytest.raises(botocore.exceptions.ClientError):
            put_record(queue=queue, record=fixture)

    def test_fail_to_send(self, set_environment):
        queue = Queue(type=QueueType.SQS, path="FOO", url="badqueue")
        fixture = {"path": queue.path, "kwargs": {}}
        with pytest.raises(exceptions.FailCatastrophically):
            put_record(queue=queue, record=fixture)


def test_invalid_queue(set_environment):
    with pytest.raises(exceptions.InvalidConfigurationError):
        process_event(
            event=None,
            context=b3f.awslambda.MockContext(function_name=config("FUNCTION_NAME")),
            paths=None,
            queue_type="badqueue",
        )


def test_fail_catastrophically(set_environment):
    def _fail(**kwargs):
        raise exceptions.FailCatastrophically()

    with pytest.raises(exceptions.FailCatastrophically):
        process_event(
            event=[{"foo": "bar"}],
            context=b3f.awslambda.MockContext(function_name=config("FUNCTION_NAME")),
            paths={"FAIL": [Action(functions=[_fail])]},
            queue_type=QueueType.RAW,
            default_path="FAIL",
        )


@pytest.mark.usefixtures("sqs", "kinesis")
class TestProcessEvents:
    @pytest.mark.parametrize(
        "queue_name,queue",
        [
            ("raw", {"type": QueueType.RAW, "encoder": testing.raw_payload}),
            ("sqs", {"type": QueueType.SQS, "encoder": testing.sqs_payload}),
            (
                "kinesis",
                {"type": QueueType.KINESIS, "encoder": testing.kinesis_payload},
            ),
        ],
    )
    @pytest.mark.parametrize(
        "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
    )
    def test_process_event(
        self, set_environment, fixture_name, fixture, queue_name, queue
    ):
        from dummy_lambda.func.main import Path, PATHS

        kwargs = {}
        if fixture.get("path", None):
            kwargs["default_path"] = fixture["path"]

        response = process_event(
            event=queue["encoder"](fixture["payload"]),
            context=b3f.awslambda.MockContext(function_name=config("FUNCTION_NAME")),
            path_enum=Path,
            paths=PATHS,
            queue_type=queue["type"],
            debug=True,
            exception_handler=exception_handler,
            **kwargs
        )
        b3f.utils.emit_logs(response)
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
            str(path).split(".")[-1]: [
                a.copy() if isinstance(a, Action) else a for a in actions
            ]
            for path, actions in deepcopy(PATHS).items()
        }

        kwargs = {}
        if fixture.get("path", None):
            kwargs["default_path"] = fixture["path"]

        response = process_event(
            event=testing.raw_payload(fixture["payload"]),
            context=b3f.awslambda.MockContext(function_name=config("FUNCTION_NAME")),
            paths=_PATHS,
            queue_type=QueueType.RAW,
            debug=True,
            **kwargs
        )
        b3f.utils.emit_logs(response)
        for k, v in fixture["response"].items():
            assert response[k] == v

    @pytest.mark.parametrize(
        "queue_name,queue",
        [
            ("raw", {"type": QueueType.RAW, "encoder": testing.raw_payload}),
            ("sqs", {"type": QueueType.SQS, "encoder": testing.sqs_payload}),
            (
                "kinesis",
                {"type": QueueType.KINESIS, "encoder": testing.kinesis_payload},
            ),
        ],
    )
    def test_process_event_fixed_function(self, set_environment, queue_name, queue):
        from dummy_lambda.func.main import test_func

        response = process_event(
            event=queue["encoder"]({"foo": "bar"}),
            context=b3f.awslambda.MockContext(function_name=config("FUNCTION_NAME")),
            call=test_func,
            queue_type=queue["type"],
            debug=True,
        )
        b3f.utils.emit_logs(response)
        # cannibalizing a fixture for this one-off test
        fixture_response = {"stats": {"received": 1, "successes": 0}}
        for k, v in fixture_response.items():
            assert response[k] == v
