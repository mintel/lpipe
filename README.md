# lpipe

**lpipe** provides a simple set of tools for writing well defined, multi-function AWS Lambdas in Python.




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
          	required_params=["foo"],
          	functions=[test_func],
          	paths=[]
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

| Argument          | Description                     |
| ----------------- | ------------------------------- |
| `required_params` | A list of kwarg keys to expect. |
| `functions` | A list of functions to run with the provided kwargs. |
| `paths` | A list of path names (to be run in the current lambda instance) or Queues to push messages to. |


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

| Argument          | Description                     |
| ----------------- | ------------------------------- |
| `type` | Instance of lpipe.pipeline.QueueType                         |
| `name` | Name/identifier/ARN of the queue                             |
| `path` | A path name, usually to trigger a path in the lambda feeding off of this queue. |

##### Example

```python
from lpipe.pipeline import Queue, QueueType

Queue(
		type=QueueType.KINESIS,
  	name="my-stream-name",
  	path="DO_THING"
)
```

