# lpipe
[![PyPI version](https://img.shields.io/pypi/v/lpipe.svg)](https://pypi.org/project/lpipe/) [![TravisCI build status](https://travis-ci.com/mintel/lpipe.svg?branch=master)](https://travis-ci.com/github/mintel/lpipe) [![Code Coverage](https://img.shields.io/codecov/c/github/mintel/lpipe.svg)](https://codecov.io/gh/mintel/lpipe)

**lpipe** provides a simple set of tools for writing clearly defined, multi-function AWS Lambdas in Python.

This project was born out of a desire to support directed-graph workflows on FAAS. **lpipe** is designed to handle batched events from CloudWatch, Kinesis, or SQS.

#### Features

* Batch message handling
* Error handling and capture - distinguish exceptions which should poison the queue
* Validate messages against function signatures
* Automatically handle partial failures in a batch of messages (SQS)
* Create directed graph workflows with a combination of one or more lambdas (*optional*)


## Getting Started

#### Basic Example

```python
import lpipe

def test_func(foo: str, **kwargs):
	pass

def lambda_handler(event, context):
    return lpipe.process_event(
        event=event,
        context=context,
        call=test_func,
        queue_type=lpipe.QueueType.SQS,
    )
```

This lambda could now be triggered by an SQS queue with the following message.

```python
{
  "foo": "bar",
}
```



#### Optionally, create a directed-graph workflow

You may also split your lambda into reusable chunks by defining paths.

```python
def lambda_handler(event, context):
    return lpipe.process_event(
        event=event,
        context=context,
        paths={
            "EXAMPLE": [test_func]
        },
        queue_type=lpipe.QueueType.SQS,
    )
```

Trigger with...

```python
{
  "path": "EXAMPLE",
  "kwargs": {
    "foo": "bar",
  }
}
```

There are two tools which enable a directed workflow.

* [Actions](#actions): A path may be defined as a `List[Action]` containing any functions, paths, or queues

* [Payloads](#payloads): Your function may return a `Payload` or `List[Payload]` which will be sequentially executed before continuing

See the linked sections in "Advanced" for more details.



## Message Structure

There are two message formats you will encounter.

#### Basic

lpipe will expect this structure if you call it via...

* `process_event(call: FunctionType)`
* `process_event(paths: dict, default_path: Union[str, Enum])`

```json
{
  "foo": "bar",
}
```

#### Directed Graph

lpipe will expect this structure if you call it via...

* `process_event(paths: dict)`

```json
{
  "path": "EXAMPLE",
  "kwargs": {
    "foo": "bar",
  }
}
```



## Batch Processing

### SQS

When processing messages from an SQS queue, we will wait to raise any errors until all the messages in a batch are tried.
* Successful Records will be deleted from the invoking queue
* Failed records will raise an exception which ultimately triggers the SQS redrive policy.

### Everything else...

**If you're using any other invocation source, please consider setting your batch size to 1.**



## Handling Errors

`lpipe` relies on exceptions for flow control. Your code must raise exceptions that inherit from one of two classes.

### `FailCatastrophically`

Raise this if you want your lambda to error out. This will result in poisoned records persisting on the queue if you're not careful. Only use it if you have CRITICAL data in the queue *or* if you hit an error state while setting up. This will trigger your redrive or DLQ policy.

| Exception | Description |
| - | - |
| InvalidConfigurationError(FailCatastrophically) | Raised automatically if your lambda is misconfigured. |

### `FailButContinue`

Raise this to log an exception and, optionally, send it to sentry, but continue processing more records. **This will treat your record as poisoned and will drop it.**

| Exception | Description |
| - | - |
| InvalidPathError(FailButContinue) | Raised automatically if you use a Path that was not defined. |
| InvalidPayloadError(FailButContinue) | Raised automatically if your lambda receives a message that is malformed or invalid. |

### Everything else...

Any errors that don't inherit from one of the two classes above will be logged and captured at sentry (if initialized.) Your record will then be dropped to prevent a poisoned queue.



## Advanced

#### Paths

A path is defined by an enumerated name and a list of actions or functions.

##### Example

```python
from enum import Enum
from lpipe import Action

class Path(Enum):
	DO_THING = 1

PATHS = {
    Path.DO_THING: [
        Action(required_params=[], functions=[], paths=[]),
      	Action(required_params=[], functions=[], paths=[]),
    ],
}
```

`lpipe` can also generate the enumeration for you automatically...

```python
PATHS = {
    "DO_THING": [
        Action(required_params=[], functions=[], paths=[]),
      	Action(required_params=[], functions=[], paths=[]),
    ],
}
```

A list of functions is also an acceptable path definition.
```python
PATHS = {
    "DO_THING": [my_function, my_second_function],
}
```



#### Actions

```python
lpipe.Action(required_params, functions, paths)
```

| Argument          | Type | Description                     |
| ----------------- | ---- | ------------------------------- |
| `required_params` | `list` | (optional if functions is set, required if ONLY paths is set) A list of kwarg keys to expect. |
| `functions` | `list` | (optional if paths is set) A list of functions to run with the provided kwargs. |
| `paths` | `list` | (optional if functions is set) A list of path names (to be run in the current lambda instance) or Queues to push messages to. |
| `include_all_params` | `bool` | If true, pass all kwargs to every function/path in this Action. |

##### Example

```python
from lpipe import Action

Action(
    required_params=["name", "email"],
    functions=[subscribe_to_pewdiepie],
    paths=[SEND_MERCH]
)
```

Using this action would first call `subscribe_to_pewdiepie(name, email)` then try to run the `SEND_MERCH` path.

`required_params` [is optional](#params) if you define type hints on your function.
```python
def subscribe_to_pewdiepie(name: str, email: str, **kwargs):
	pass

Action(
    functions=[subscribe_to_pewdiepie],
    paths=[SEND_MERCH]
)
```



#### Defining Parameters

Parameters can be inferred from your function signatures or explicitly set. If you allow parameters to be inferred, default values are permitted, and type hints will be enforced.

##### Example
```python
def test_func(foo: str, bar: int = 42, **kwargs):
	pass

Path.MY_PATH: [
    Action(
        functions=[my_func],  # IMPLICIT
    )
],
```

**OR**

```python
def test_func(foo, bar, **kwargs):
	pass

Path.MY_PATH: [
    Action(
        required_params=["foo", "bar"],  # EXPLICIT
        functions=[my_func],
    )
],
```



#### Queues

```python
lpipe.Queue(type, name, path)
```

| Argument          | Type | Description                     |
| ----------------- | ---- | ------------------------------- |
| `type` | `lpipe.QueueType` | |
| `name` | `str` | Name/identifier of the queue (used by `QueueType.Kinesis`, `QueueType.SQS`) If you include name instead of url for an SQS queue, the queue URL will fetched automatically. |
| `url`  | `str` | URL/URI of the queue (used by `QueueType.SQS`) |
| `path` | `str` | (optional) A path name, usually to trigger a path in the lambda feeding off of this queue. If this is set, the sent message will be in the standard lpipe format of `{"path": "", "kwargs": {}}`.|

##### Example

```python
from lpipe import Queue, QueueType

Queue(type=QueueType.SQS, name="my-queue-name")
```



#### Payloads

If you return `Payload` or `List[Payload]` from a function called by lpipe, the payloads will be sequentially executed before proceeding with other messages. Keep time restrictions in mind when using this feature.

```python
lpipe.Payload(kwargs, path, queue, event_source)
```

| Argument       | Type            | Description                                                 |
| -------------- | --------------- | ----------------------------------------------------------- |
| `kwargs`       | `dict`          |                                                             |
| `path`         | `Enum` or `str` | Optional if `queue` is set                                  |
| `queue`        | `lpipe.Queue`   | Optional if `path` is set                                   |
| `event_source` | `str`           | (optional) Set automatically on Payloads generated by lpipe |

##### Example

```python
from lpipe import Payload

Payload(
    kwargs={"lorem": "ipsum"},
    path="MY_PATH",
)
```



## Advanced Example

Combining all of the features documented above will allow you to chain messages through a directed graph of local code and remote services.

This example demonstrates a lambda with two functions. Both can be triggered directly by a message, but one will trigger the other.

```python
import lpipe

def my_func(foo: str, **kwargs):
	pass

def my_generic_func(foo: str, **kwargs):
	# pseudo code
    data = request.get(os.environ["MY_API_URL"], {"foo": foo})
    # queue up message with another service
    return lpipe.Payload(
      kwargs=data,
      queue=lpipe.Queue(
          type=lpipe.QueueType.SQS,
          name="my-service-queue",
      ),
  )

PATHS = {
    "FIRST_PATH": [
        Action(functions=[my_func], paths=["GENERIC_REUSABLE_PATH"]),
    ],
    "GENERIC_REUSABLE_PATH": [my_generic_func],
}

def lambda_handler(event, context):
    return lpipe.process_event(
        event=event,
        context=context,
        paths=PATHS,
        queue_type=lpipe.QueueType.SQS,
    )
```

Trigger with...

```python
{
    "path": "FIRST_PATH",
    "kwargs": {
        "foo": "bar",
    }
}
```
