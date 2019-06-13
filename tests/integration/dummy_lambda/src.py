def test_func(foo, logger, **kwargs):
    if not foo:
        raise Exception("Missing required parameter 'foo'")
    logger.log("test_func success")
    return True


def test_func_no_params(logger, **kwargs):
    logger.log("test_func_no_params success")
    return True
