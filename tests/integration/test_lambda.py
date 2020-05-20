# These tests have been disabled because they don't add any additional value.
# Testing the test fixtures for localstack will be moved to a new project.

# import pytest
# from decouple import config
# from tests import fixtures
#
# from lpipe.testing import invoke_lambda, sqs_payload
#
#
# @pytest.mark.postbuild
# @pytest.mark.usefixtures("sqs", "kinesis", "lam")
# class TestMockLambda:
#     @pytest.mark.parametrize(
#         "fixture_name,fixture", [(k, v) for k, v in fixtures.DATA.items()]
#     )
#     def test_lambda_fixtures(self, set_environment, fixture_name, fixture):
#         payload = sqs_payload(fixture["payload"])
#         response, body = invoke_lambda(name=config("FUNCTION_NAME"), payload=payload)
#         for k, v in fixture["response"].items():
#             assert body[k] == v
