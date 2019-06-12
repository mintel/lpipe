import pytest

from lpipe import kinesis

KINESIS_STREAMS = ["test_stream"]


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "kinesis")
class TestPutRecords:
    def test_batch_put_records_single(self, kinesis_streams):
        responses = kinesis.batch_put_records(
            stream_name=kinesis_streams[0],
            records=[{"foo": "bar", "wiz": "bang"}],
            batch_size=2,
        )
        assert len(responses) == 1
        assert (
            all([r["ResponseMetadata"]["HTTPStatusCode"] == 200 for r in responses])
            == True
        )

    def test_batch_put_records_many(self, kinesis_streams):
        responses = kinesis.batch_put_records(
            stream_name=kinesis_streams[0],
            records=[
                {"foo": "bar", "wiz": "bang"},
                {"lorem": "ipsum", "quid": "est"},
                {"foo": "bar", "wiz": "bang"},
                {"lorem": "ipsum", "quid": "est"},
            ],
            batch_size=2,
        )
        assert len(responses) == 2
        assert (
            all([r["ResponseMetadata"]["HTTPStatusCode"] == 200 for r in responses])
            == True
        )

    def test_batch_put_record(self, kinesis_streams):
        responses = kinesis.put_record(
            stream_name=kinesis_streams[0], data={"foo": "bar", "wiz": "bang"}
        )
        assert len(responses) == 1
        assert (
            all([r["ResponseMetadata"]["HTTPStatusCode"] == 200 for r in responses])
            == True
        )
