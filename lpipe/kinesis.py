import json
import logging
from functools import wraps

import boto3
import botocore
from decouple import config

from lpipe.utils import batch, hash


def build(record_data):
    data = json.dumps(record_data, sort_keys=True)
    return {"Data": data, "PartitionKey": hash(data)}


def mock_kinesis(func):
    @wraps(func)
    def wrapper(stream_name, records, *args, **kwargs):
        try:
            return func(stream_name, records, *args, **kwargs)
        except (
            botocore.exceptions.NoCredentialsError,
            botocore.exceptions.ClientError,
            botocore.exceptions.NoRegionError,
        ):
            if config("MOCK_AWS", default=False):
                log = kwargs["logger"] if "logger" in kwargs else logging.getLogger()
                if records:
                    for r in records:
                        log.debug(
                            "kinesis.put_records: mocked stream:{} data:{}".format(
                                stream_name, build(r)
                            )
                        )
                else:
                    log.warning("kinesis.put_records: no records provided")
                return
            else:
                raise

    return wrapper


@mock_kinesis
def batch_put_records(stream_name, records, batch_size=500, **kwargs):
    """Put records into a kinesis stream, batched by the maximum of 500."""
    client = boto3.client("kinesis")
    responses = []
    for b in batch(records, batch_size):
        response = client.put_records(
            StreamName=stream_name, Records=[build(record) for record in b]
        )
        responses.append(response)
    return tuple(responses)


def put_record(stream_name, data, **kwargs):
    return batch_put_records(stream_name=stream_name, records=[data])
