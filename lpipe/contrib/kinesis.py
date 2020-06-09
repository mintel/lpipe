import json
import logging
from functools import wraps

import botocore
from decouple import config

import lpipe.contrib.boto3
from lpipe import utils


def build(record_data):
    data = json.dumps(record_data, sort_keys=True)
    return {"Data": data, "PartitionKey": utils.hash(data)}


def mock_kinesis(func):
    @wraps(func)
    def wrapper(stream_name, records, *args, **kwargs):
        try:
            return func(stream_name, records, *args, **kwargs)
        except (
            botocore.exceptions.NoCredentialsError,
            botocore.exceptions.ClientError,
            botocore.exceptions.NoRegionError,
            botocore.exceptions.ParamValidationError,
        ):
            if config("MOCK_AWS", default=False):
                log = kwargs["logger"] if "logger" in kwargs else logging.getLogger()
                log.debug(
                    "Mocked Kinesis",
                    function=f"{func}",
                    params={"args": f"{args}", "kwargs": f"{kwargs}"},
                )
                return
            else:
                raise

    return wrapper


@mock_kinesis
def batch_put_records(stream_name, records, batch_size=500, **kwargs):
    """Put records into a kinesis stream, batched by the maximum of 500."""
    client = lpipe.contrib.boto3.client("kinesis")
    responses = []
    for b in utils.batch(records, batch_size):
        responses.append(
            utils.call(
                client.put_records,
                StreamName=stream_name,
                Records=[build(record) for record in b],
            )
        )
    return tuple(responses)


def put_record(stream_name, data, **kwargs):
    return batch_put_records(stream_name=stream_name, records=[data])
