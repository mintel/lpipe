import json
from pathlib import Path

import boto3

from .. import utils


def create_lambda(
    name: str = "my_lambda",
    runtime: str = "python3.8",
    role: str = "foobar",
    handler: str = "main.lambda_handler",
    path: str = "dummy_lambda/dist/build.zip",
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

    client = boto3.client("lambda")
    with open(str(Path().absolute() / path), "rb") as f:
        zipped_code = f.read()
        utils.call(
            client.create_function,
            FunctionName=name,
            Runtime=runtime,
            Role=role,
            Handler=handler,
            Code=dict(ZipFile=zipped_code),
            Timeout=300,
            Environment={"Variables": clean_env(environment)},
        )


def destroy_lambda(name: str = "my_lambda"):
    client = boto3.client("lambda")
    return utils.call(client.delete_function, FunctionName=name)


def invoke_lambda(name: str, payload: dict, invocation_type="RequestResponse"):
    client = boto3.client("lambda")
    response = utils.call(
        client.invoke,
        FunctionName=name,
        InvocationType=invocation_type,
        LogType="Tail",
        Payload=json.dumps(payload).encode(),
    )
    body = response["Payload"].read().decode("utf-8")
    try:
        body = json.loads(body)
    except:
        pass
    return response, body
