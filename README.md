# lpipe ![](https://travis-ci.com/mintel/lpipe.svg?branch=master)

**lpipe** provides a simple set of tools for writing clearly defined, multi-function AWS Lambdas in Python.

This project was borne out of a desire to support directed-graph workflows on FAAS. **lpipe** is designed to handle batched events from CloudWatch, Kinesis, or SQS.



## Getting Started

At its most basic, your lambda would require no more than this.

```python
import lpipe

def test_func(foo: str, **kwargs):
	pass

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

This lambda could now be triggered from a kinesis stream input with the following message.

```python
{
  "path": "EXAMPLE",
  "kwargs": {
    "foo": "bar",
  }
}
```



## Flow Control

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



## Batch Processing

### SQS

When processing messages from an SQS queue, we will wait to raise any errors until all the messages in a batch are tried.
* Successful Records will be deleted from the invoking queue
* Failed records will raise an exception which ultimately triggers the SQS redrive policy.

### Everything else...

If you're using any other invocation method, please consider setting your batch size to 1.



## Advanced

#### Paths

A path is defined by an enumerated name and a list of actions.

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

`lpipe` can also handle this for you automatically...

```python
from lpipe import Action

PATHS = {
    "DO_THING": [
        Action(required_params=[], functions=[], paths=[]),
      	Action(required_params=[], functions=[], paths=[]),
    ],
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



#### Queues

```python
lpipe.Queue(type, name, path)
```

| Argument          | Type | Description                     |
| ----------------- | ---- | ------------------------------- |
| `type` | `lpipe.pipeline.QueueType` | |
| `name` | `str` | Name/identifier/ARN of the queue |
| `path` | `str` | A path name, usually to trigger a path in the lambda feeding off of this queue. |

##### Example

```python
from lpipe import Queue, QueueType

Queue(
	type=QueueType.KINESIS,
  	name="my-stream-name",
  	path="DO_THING"
)
```



#### Params

Parameters can be inferred from your function signatures or explicitly set. If you allow parameters to be inferred, default values are permitted, and type hints will be enforced.

##### Example
```python
def test_func(foo: str, bar: int = 42, **kwargs):
	pass

Path.MY_PATH: [
    Action(
        functions=[my_func],
    )
],
```

**OR**

```python
def test_func(foo, bar, **kwargs):
	pass

Path.MY_PATH: [
    Action(
        required_params=["foo", "bar"],
        functions=[my_func],
    )
],
```
