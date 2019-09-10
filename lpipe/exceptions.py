class InvalidTaxonomyURI(Exception):
    pass


class GraphQLError(Exception):
    pass


class FailButContinue(Exception):
    """Raise this in your lambda if you want to break with an error but continue processing."""

    pass


class FailCatastrophically(Exception):
    """Raise this in your lambda if you want the lambda to error out completely."""

    pass


class InvalidInputError(Exception):
    pass


class InvalidPathError(Exception):
    pass


class InvalidPayload(Exception):
    pass
