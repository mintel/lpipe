import base64
import json
import logging

import pytest
import boto3
import hashlib
import functools
from botocore.exceptions import ClientError

import lpipe


LOGGER = logging.getLogger()


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "dummy_lambda")
class TestDummyLambda:
    def test_lambda_sanity(self):
        pass

    def test_lambda_empty_no_payload(self, invoke_lambda, kinesis_payload):
        payload = []
        response, body = invoke_lambda(name="dummy_lambda", payload=kinesis_payload(payload))
        assert response["StatusCode"] // 100 == 2

    def test_lambda_empty_payload(self, invoke_lambda, kinesis_payload):
        payload = [{}]
        with pytest.raises(ClientError):
            response, body = invoke_lambda(name="dummy_lambda", payload=kinesis_payload(payload))

    def test_lambda_func(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_FUNC", "kwargs": {"foo": "bar"}}]
        response, body = invoke_lambda(name="dummy_lambda", payload=kinesis_payload(payload))
        assert response["StatusCode"] // 100 == 2
