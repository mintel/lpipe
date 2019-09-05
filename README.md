# lpipe

**lpipe** provides a simple set of tools for writing clearly defined, multi-function AWS Lambdas in Python.

This project was borne out of a desire to support directed-graph workflows on FAAS. **lpipe** is designed to handle batched events from CloudWatch, Kinesis, or SQS.




## Getting Started

At its most basic, your lambda would require no more than this.

```python
from enum import Enum
from lpipe.pipeline import Action, Queue, QueueType, process_event

def test_func(foo, **kwargs):
	pass

class Path(Enum):
    EXAMPLE = 1

PATHS = {
    Path.EXAMPLE: [
      	Action(
          	functions=[test_func],
        )
    ],
}

def lambda_handler(event, context):
    return process_event(
        event=event,
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
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



## Advanced

#### Paths

A path is defined by an enumerated name and a list of actions.

##### Example

```python
from enum import Enum
from lpipe.pipeline import Action

class Path(Enum):
	DO_THING = 1

PATHS = {
    Path.DO_THING: [
        Action(required_params=[], functions=[], paths=[]),
      	Action(required_params=[], functions=[], paths=[]),
    ],
}
```



#### Actions

```python
lpipe.pipeline.Action(required_params, functions, paths)
```

| Argument          | Type | Description                     |
| ----------------- | ---- | ------------------------------- |
| `required_params` | `list` | (optional if functions is set, required if ONLY paths is set) A list of kwarg keys to expect. |
| `functions` | `list` | (optional if paths is set) A list of functions to run with the provided kwargs. |
| `paths` | `list` | (optional if functions is set) A list of path names (to be run in the current lambda instance) or Queues to push messages to. |

##### Example

```python
from lpipe.pipeline import Action

Action(
    required_params=["name", "email"],
    functions=[subscribe_to_pewdiepie],
    paths=[SEND_MERCH]
)
```

Using this action would first call `subscribe_to_pewdiepie(name, email)` then try to run the `SEND_MERCH` path.



#### Queues

```python
lpipe.pipeline.Queue(type, name, path)
```

| Argument          | Type | Description                     |
| ----------------- | ---- | ------------------------------- |
| `type` | `lpipe.pipeline.QueueType` | |
| `name` | `str` | Name/identifier/ARN of the queue |
| `path` | `str` | A path name, usually to trigger a path in the lambda feeding off of this queue. |

##### Example

```python
from lpipe.pipeline import Queue, QueueType

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
