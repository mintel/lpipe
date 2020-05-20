import pytest

import lpipe.contrib.boto3
from lpipe import utils


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("valid_empty", {"input": "", "output": {}, "raises": None}),
        ("valid", {"input": "a=b,c=d", "output": {"a": "b", "c": "d"}, "raises": None}),
        ("invalid", {"input": "asdf", "output": None, "raises": ValueError}),
    ],
)
def test_to_dict(fixture_name, fixture):
    raises = fixture.get("raises", None)
    if raises:
        with pytest.raises(raises):
            output = lpipe.contrib.boto3._to_dict(fixture["input"])
    else:
        output = lpipe.contrib.boto3._to_dict(fixture["input"])
        assert output == fixture["output"]


region_name = "us-east-1"
fixtures = [
    ("no_url", {"region_name": region_name}),
    ("none_url", {"region_name": region_name, "endpoint_url": None}),
    ("url", {"region_name": region_name, "endpoint_url": "http://localstack:1234"}),
]
client_services = ["sqs", "kinesis", "dynamodb", "s3", "lambda"]
resource_services = ["sqs"]


@pytest.mark.parametrize("service_name", client_services)
@pytest.mark.parametrize("fixture_name,fixture", fixtures)
def test_client(fixture_name, fixture, service_name, environment):
    endpoint_url = fixture.get("endpoint_url", None)
    env = {}
    if endpoint_url:
        env["AWS_ENDPOINTS"] = service_name + "=" + endpoint_url
    with utils.set_env(env):
        client = lpipe.contrib.boto3.client(service_name, **fixture)
        if endpoint_url:
            assert client.meta.endpoint_url == endpoint_url


@pytest.mark.parametrize("service_name", client_services)
@pytest.mark.parametrize("fixture_name,fixture", fixtures)
def test_client_no_env(fixture_name, fixture, service_name):
    endpoint_url = fixture.get("endpoint_url", None)
    client = lpipe.contrib.boto3.client(service_name, **fixture)
    if endpoint_url:
        assert client.meta.endpoint_url == endpoint_url


@pytest.mark.parametrize("service_name", resource_services)
@pytest.mark.parametrize("fixture_name,fixture", fixtures)
def test_resource(fixture_name, fixture, service_name, environment):
    endpoint_url = fixture.get("endpoint_url", None)
    env = {}
    if endpoint_url:
        env["AWS_ENDPOINTS"] = service_name + "=" + endpoint_url
    with utils.set_env(env):
        resource = lpipe.contrib.boto3.resource(service_name, **fixture)
        assert resource.meta.service_name == service_name
        client = resource.meta.client
        if endpoint_url:
            assert client.meta.endpoint_url == endpoint_url


@pytest.mark.parametrize("service_name", resource_services)
@pytest.mark.parametrize("fixture_name,fixture", fixtures)
def test_resource_no_env(fixture_name, fixture, service_name):
    endpoint_url = fixture.get("endpoint_url", None)
    resource = lpipe.contrib.boto3.resource(service_name, **fixture)
    assert resource.meta.service_name == service_name
    client = resource.meta.client
    if endpoint_url:
        assert client.meta.endpoint_url == endpoint_url
