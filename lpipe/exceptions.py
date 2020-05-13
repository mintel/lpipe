class LpipeBaseException(Exception):
    pass


# FLOW CONTROL
class FailButContinue(LpipeBaseException):
    pass


class FailCatastrophically(LpipeBaseException):
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


# OTHER
class InvalidTaxonomyURI(Exception):
    pass


class GraphQLError(Exception):
    pass
