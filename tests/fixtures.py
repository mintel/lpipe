ENV = {"AWS_DEFAULT_REGION": "us-east-2", "FUNCTION_NAME": "my_lambda"}

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
    "FUNC_EXPLICIT_PARAMS": {
        "payload": [{"path": "TEST_FUNC_EXPLICIT_PARAMS", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "FUNC_NO_PARAMS": {
        "payload": [{"path": "TEST_FUNC_NO_PARAMS", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "FUNC_BLANK_PARAMS": {
        "payload": [{"path": "TEST_FUNC_BLANK_PARAMS", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "FUNC_LOWER_CASE": {
        "payload": [{"path": "test_func", "kwargs": {"foo": "bar"}}],
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
    "MULTI_FUNC": {
        "payload": [{"path": "MULTI_TEST_FUNC", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "MULTI_FUNC_NO_PARAMS": {
        "payload": [{"path": "MULTI_TEST_FUNC_NO_PARAMS", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "TEST_BARE_FUNCS": {
        "payload": [{"path": "TEST_FUNC", "kwargs": {"foo": "bar"}}],
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
    "SQS_OUTPUT": {
        "payload": [{"path": "TEST_SQS_PATH", "kwargs": {"uri": "foo"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "DEFAULT_PARAM": {
        "payload": [{"path": "TEST_FUNC_DEFAULT_PARAM", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "DEFAULT_PARAM_SET": {
        "payload": [{"path": "TEST_FUNC_DEFAULT_PARAM", "kwargs": {"foo": "wiz"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    # "SENTRY_ERROR": {
    #     "payload": [{"path": "TEST_SENTRY", "kwargs": {}}],
    #     "response": {"stats": {"received": 1, "successes": 0}},
    # },
    "MANUAL_OUTPUT": {
        "payload": [{"path": "TEST_RET", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}, "output": ["foobar"]},
    },
    "TRIGGER_PATH_WITH_RETURN": {
        "payload": [{"path": "TEST_TRIGGER_FIRST", "kwargs": {}}],
        "response": {"stats": {"received": 1, "successes": 1}, "output": ["foobar"]},
    },
    "MULTI_TRIGGER_PATH": {
        "payload": [{"path": "TEST_MULTI_TRIGGER", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "TRIGGER_PATH_WITH_ERROR": {
        "payload": [{"path": "TEST_TRIGGER_ERROR", "kwargs": {"foo": "bar"}}],
        "response": {"stats": {"received": 1, "successes": 0}},
    },
    "DEFAULT_PATH_FUNC": {
        "path": "TEST_FUNC",
        "payload": [{"foo": "bar"}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "DEFAULT_PATH_FUNC_MANY": {
        "path": "TEST_FUNC",
        "payload": [{"foo": "bar"}, {"foo": "bar"}, {"foo": "bar"}],
        "response": {"stats": {"received": 3, "successes": 3}},
    },
    "DEFAULT_PATH_KWARGS_PASSED": {
        "path": "TEST_DEFAULT_PATH",
        "payload": [{"foo": "bar"}],
        "response": {"stats": {"received": 1, "successes": 1}},
    },
    "DEFAULT_PATH_KWARGS_PASSED_ERROR": {
        "path": "TEST_DEFAULT_PATH",
        "payload": [{"wiz": "bang"}],
        "response": {"stats": {"received": 1, "successes": 0}},
    },
}
