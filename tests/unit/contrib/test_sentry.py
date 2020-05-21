from lpipe.contrib import sentry


def test_init(set_environment):
    sentry.init(context={"foo": "bar"})


def test_get_env(set_environment):
    assert sentry._env("ASDF") is None
    assert sentry._env("ASDF", "FUNCTION_NAME") == "my_lambda"


def test_push_context(set_environment):
    @sentry.push_context({"FOO": "BAR"})
    def _test_func():
        return True

    assert _test_func()


def test_capture_exception(set_environment):
    try:
        raise Exception("Test event. Please ignore.")
    except Exception as e:
        sentry.capture(e)
