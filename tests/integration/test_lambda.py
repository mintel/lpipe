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


def _emit_logs(body):
    if "logs" in body:
        for log in body["logs"]:
            LOGGER.log(level=logging.INFO, msg=log["event"])


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "dummy_lambda")
class TestDummyLambda:
    def test_lambda_sanity(self):
        pass

    def test_lambda_empty_no_payload(self, invoke_lambda, kinesis_payload):
        payload = []
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 0
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_empty_payload(self, invoke_lambda, kinesis_payload):
        payload = [{}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["successes"] == 0

    def test_lambda_func(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_FUNC", "kwargs": {"foo": "bar"}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_func_no_params(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_FUNC_NO_PARAMS", "kwargs": {}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_path(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_PATH", "kwargs": {"foo": "bar"}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_func_and_path(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_FUNC_AND_PATH", "kwargs": {"foo": "bar"}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_multi_func_no_params(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "MULTI_TEST_FUNC_NO_PARAMS", "kwargs": {}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_rename_param(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_RENAME_PARAM", "kwargs": {"bar": "bar"}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]

    def test_lambda_kinesis(self, invoke_lambda, kinesis_payload):
        payload = [{"path": "TEST_KINESIS_PATH", "kwargs": {"uri": "foo"}}]
        response, body = invoke_lambda(
            name="dummy_lambda", payload=kinesis_payload(payload)
        )
        _emit_logs(body)
        assert response["StatusCode"] // 100 == 2
        assert body["stats"]["received"] == 1
        assert body["stats"]["received"] == body["stats"]["successes"]
