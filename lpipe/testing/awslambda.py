"""
Example Usage

```python
@pytest.fixture(scope="class")
def lam(localstack, environment):
    yield lpipe.testing.create_lambda(
        runtime="python3.6",
        environment=environment(MOCK_AWS=True),
    )
    lpipe.testing.destroy_lambda()

@pytest.mark.usefixtures("lam")
def test_lambda():
    payload = [{...}, {...}]
    response, body = invoke_lambda(name="my_lambda", payload=sqs_payload(messages))
```
"""

import json
from pathlib import Path

import boto3

from .. import utils
from .utils import emit_logs


def create_lambda(
    name: str = "my_lambda",
    runtime: str = "python3.8",
    role: str = "foobar",
    handler: str = "main.lambda_handler",
    path: str = "dist/build.zip",
    environment: dict = {},
):
    def clean_env(env):
        for k, v in env.items():
            if isinstance(v, bool):
                if v:
                    env[k] = str(v)
                else:
                    continue
            elif isinstance(v, type(None)):
                env[k] = ""
        return env

    with open(str(Path().absolute() / path), "rb") as f:
        zipped_code = f.read()
        utils.call(
            boto3.client("lambda").create_function,
            FunctionName=name,
            Runtime=runtime,
            Role=role,
            Handler=handler,
            Code=dict(ZipFile=zipped_code),
            Timeout=300,
            Environment={"Variables": clean_env(environment)},
        )


def destroy_lambda(name: str = "my_lambda"):
    return utils.call(boto3.client("lambda").delete_function, FunctionName=name)


def invoke_lambda(name: str, payload: dict, **kwargs):
    defaults = {
        "InvocationType": "RequestResponse",
        "LogType": "Tail",
        "Payload": json.dumps(payload).encode(),
    }
    response = utils.call(
        boto3.client("lambda").invoke,
        keys=["StatusCode"],
        **{**defaults, **kwargs, "FunctionName": name}
    )
    body = response["Payload"].read().decode("utf-8")
    try:
        body = json.loads(body)
    except:
        pass
    emit_logs(body)
    return response, body
