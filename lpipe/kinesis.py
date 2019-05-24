import functools
import hashlib
import json
import logging

import boto3
import botocore
from decouple import config

from lpipe.utils import batch


def hash(encoded_data):
    return hashlib.sha1(encoded_data.encode("utf-8")).hexdigest()


def batch_put_records(stream_name, records, batch_size=500):
    """Put records into a kinesis stream, batched by the maximum of 500."""
    client = boto3.client("kinesis")

    def build(r):
        data = json.dumps(r, sort_keys=True)
        return {"Data": data, "PartitionKey": hash(data)}

    output = []
    for b in batch(records, batch_size):
        result = client.put_records(
            StreamName=stream_name, Records=[build(record) for record in b]
        )
        output.append(result)
    return tuple(output)


def put_record(stream_name, data, **kwargs):
    return batch_put_records(stream_name=stream_name, records=[data])
