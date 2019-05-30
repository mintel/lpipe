import base64
import json

import pytest
import boto3
import hashlib
import functools

import lpipe


@pytest.mark.postbuild
@pytest.mark.usefixtures("dummy_lambda")
class TestDummyLambda:
    def test_lambda_sanity(self):
        pass

    def test_lambda_empty_payload(self, invoke_lambda, kinesis_payload):
        payload = {}
        response = invoke_lambda(name="dummy_lambda", payload=kinesis_payload(payload))
        body = response["Payload"].read()
        print(body)
        assert response["StatusCode"] // 100 == 200

    def test_lambda_func(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_FUNC", "kwargs": {"foo": "bar"}}]
        response = invoke_lambda(name="dummy_lambda", payload=kinesis_payload(payload))
        print(response)
        body = response["Payload"].read()
        print(body)
        assert response["StatusCode"] // 100 == 2
