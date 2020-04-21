import pytest
from tests.utils import (
    check_dynamodb_fixtures,
    check_kinesis_fixtures,
    check_s3_fixtures,
    check_sqs_fixtures,
)


def test_top_level_imports():
    pass


class TestMockWithMoto:
    @pytest.mark.usefixtures("kinesis_moto")
    def test_kinesis_fixtures(self, kinesis_streams):
        check_kinesis_fixtures(kinesis_streams)

    @pytest.mark.usefixtures("sqs_moto")
    def test_sqs_fixtures(self, sqs_queues):
        check_sqs_fixtures(sqs_queues)

    @pytest.mark.usefixtures("dynamodb_moto")
    def test_dynamodb_fixtures(self, dynamodb_tables):
        check_dynamodb_fixtures(dynamodb_tables)

    @pytest.mark.usefixtures("s3_moto")
    def test_s3_fixtures(self, s3_buckets):
        check_s3_fixtures(s3_buckets)
