"""
Example Usage

```python
@pytest.fixture(scope="session")
def dynamodb_tables():
    return [
        {
            "AttributeDefinitions": [
                {"AttributeName": "uri", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            "TableName": "my-dbd-table",
            "KeySchema": [
                {"AttributeName": "uri", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
        }
    ]


@pytest.fixture(scope="class")
def dynamodb(localstack, dynamodb_tables):
    try:
        yield lpipe.testing.create_dynamodb_tables(dynamodb_tables)
    finally:
        lpipe.testing.destroy_dynamodb_tables(dynamodb_tables)
```
"""

import backoff
import boto3
from botocore.exceptions import ClientError

from .. import utils


@backoff.on_exception(backoff.expo, ClientError, max_time=30)
def create_dynamodb_table(config):
    client = boto3.client("dynamodb")
    config.update({"BillingMode": "PAY_PER_REQUEST"})
    return utils.call(client.create_table, **config)


def create_dynamodb_tables(dynamodb_tables):
    client = boto3.client("dynamodb")
    for table in dynamodb_tables:
        assert create_dynamodb_table(table)
    for table in dynamodb_tables:
        waiter = client.get_waiter("table_exists")
        waiter.wait(
            TableName=table["TableName"], WaiterConfig={"Delay": 1, "MaxAttempts": 30}
        )
    return [t["TableName"] for t in dynamodb_tables]


def destroy_dynamodb_tables(dynamodb_tables):
    client = boto3.client("dynamodb")
    for table in dynamodb_tables:
        utils.call(client.delete_table, TableName=table["TableName"])
