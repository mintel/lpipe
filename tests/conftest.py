import warnings

import boto3
import pytest
import pytest_localstack

localstack = pytest_localstack.patch_fixture(
    services=["kinesis", "sqs"], scope="session", autouse=True
)


@pytest.fixture(scope="session", autouse=True)
def silence_resource_warnings():
    warnings.filterwarnings(
        action="ignore", message="unclosed", category=ResourceWarning
    )

@pytest.fixture(scope="class")
def kinesis_streams():
    return ["test_stream"]

@pytest.fixture(scope="class")
def kinesis_client():
    return boto3.client("kinesis")

@pytest.fixture(scope="class")
def kinesis(request, kinesis_client, kinesis_streams):
    print(f"Creating kinesis streams: {kinesis_streams}")
    client = kinesis_client
    try:
        for stream_name in kinesis_streams:
            client.create_stream(StreamName=stream_name, ShardCount=1)
            client.get_waiter("stream_exists").wait(
                StreamName=stream_name, WaiterConfig={"Delay": 2, "MaxAttempts": 2}
            )
        yield kinesis_streams
    finally:
        for stream_name in kinesis_streams:
            client.delete_stream(StreamName=stream_name)
            client.get_waiter("stream_not_exists").wait(
                StreamName=stream_name, WaiterConfig={"Delay": 2, "MaxAttempts": 2}
            )
