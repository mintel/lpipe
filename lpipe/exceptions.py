class LPBaseException(Exception):
    pass


# FLOW CONTROL
class FailButContinue(LPBaseException):
    pass


class FailCatastrophically(LPBaseException):
    pass


# CONFIGURATION & VALIDATION
class InvalidConfigurationError(FailCatastrophically):
    pass


class InvalidPathError(FailButContinue):
    pass


class InvalidPayloadError(FailButContinue):
    pass


# TESTING
class TestingException(Exception):
    pass
