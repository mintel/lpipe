class LambdaPipelineException(Exception):
    pass


# FLOW CONTROL
class FailButContinue(LambdaPipelineException):
    pass


class FailCatastrophically(LambdaPipelineException):
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
