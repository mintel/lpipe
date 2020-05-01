"""
Example Usage

```python
@pytest.fixture(scope="class")
def lam(localstack, environment):
    with lpipe.testing.setup_awslambda(
                runtime="python3.6",
                environment=environment(MOCK_AWS=True),
            ) as lam:
        yield lam

@pytest.mark.usefixtures("lam")
def test_lambda():
    payload = [{...}, {...}]
    response, body = invoke_lambda(name="my_lambda", payload=sqs_payload(messages))
```
"""

import json
from contextlib import contextmanager
from pathlib import Path

from .. import _boto3, utils
from .utils import emit_logs


def create_lambda(
    name: str = "my_lambda",
    runtime: str = "python3.8",
    role: str = "foobar",
    handler: str = "main.lambda_handler",
    path: str = "dist/build.zip",
    environment: dict = {},
    **kwargs,
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
            _boto3.client("lambda").create_function,
            FunctionName=name,
            Runtime=runtime,
            Role=role,
            Handler=handler,
            Code=dict(ZipFile=zipped_code),
            Timeout=300,
            Environment={"Variables": clean_env(environment)},
        )


def destroy_lambda(name: str = "my_lambda", **kwargs):
    return utils.call(_boto3.client("lambda").delete_function, FunctionName=name)


def invoke_lambda(name: str = "my_lambda", payload: dict = {}, **kwargs):
    defaults = {
        "InvocationType": "RequestResponse",
        "LogType": "Tail",
        "Payload": json.dumps(payload).encode(),
    }
    response = _boto3.client("lambda").invoke(
        FunctionName=name, **{**defaults, **kwargs}
    )
    utils.check_status(response, keys=["StatusCode"])
    body = response["Payload"].read().decode("utf-8")
    try:
        body = json.loads(body)
    except Exception:
        pass
    emit_logs(body)
    return response, body


@contextmanager
def setup_awslambda(**kwargs):
    try:
        yield create_lambda(**kwargs)
    finally:
        destroy_lambda(**kwargs)
