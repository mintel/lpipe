ENV = {}

DATA = {
    "EMPTY_NO_PAYLOAD": {
        "payload": [],
        "response": {"stats": {"received": 0, "successes": 0}},
    },
    "EMPTY_PAYLOAD": {
        "payload": [{}],
        "response": {"stats": {"received": 1, "successes": 0}},
    },
    "FUNC": {
        "payload": [{"path": "TEST_FUNC", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "FUNC_MISSING_PARAMS": {
        "payload": [{"path": "TEST_FUNC", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 0}},
    },
    "FUNC_NO_PARAMS": {
        "payload": [{"path": "TEST_FUNC_NO_PARAMS", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "PATH": {
        "payload": [{"path": "TEST_PATH", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "FUNC_AND_PATH": {
        "payload": [{"path": "TEST_FUNC_AND_PATH", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "MULTI_FUNC_NO_PARAMS": {
        "payload": [{"path": "MULTI_TEST_FUNC_NO_PARAMS", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "RENAME_PARAM": {
        "payload": [{"path": "TEST_RENAME_PARAM", "kwargs": {"bar": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "KINESIS_OUTPUT": {
        "payload": [{"path": "TEST_KINESIS_PATH", "kwargs": {"uri": "foo"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    # "SQS_OUTPUT": {"payload": [{"path": "TEST_SQS_PATH", "kwargs": {"uri": "foo"}}], "response": {"stats": {"received": 1, "successes": 1}}},
}
