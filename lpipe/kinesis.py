import hashlib
import json

import boto3


def get_kinesis_key(encoded_data):
    return hashlib.sha1(encoded_data.encode("utf-8")).hexdigest()


def put_record(stream_name, data, key=None):
    encoded_data = json.dumps(data, sort_keys=True)
    if not key:
        key = get_kinesis_key(encoded_data)
    kinesis_client = boto3.client("kinesis")
    kinesis_client.put_record(
        StreamName=stream_name, Data=encoded_data, PartitionKey=key
    )


def batch_put_records(stream_name, records, batch_size=500):
    """Put records into a kinesis stream, batched by the maximum of 500."""
    kinesis_client = boto3.client("kinesis")

    def build(r):
        data = json.dumps(r, sort_keys=True)
        return {"Data": data, "PartitionKey": get_kinesis_key(data)}

    for batch_of_records in batch(records, batch_size):
        kinesis_client.put_records(
            StreamName=stream_name,
            Records=[build(record) for record in batch_of_records],
        )
