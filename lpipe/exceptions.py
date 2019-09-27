class InvalidTaxonomyURI(Exception):
    pass


class GraphQLError(Exception):
    pass


class FailButContinue(Exception):
    """Raise this to log an exception and, optionally, send it to sentry, but continue processing more records."""

    pass


class FailCatastrophically(Exception):
    """Raise this if you want your lambda to error.

    This will often result in poisioned records persisting. Only use it if you
    have CRITICAL data in the queue.
    """

    pass


class InvalidInputError(Exception):
    pass


class InvalidPathError(Exception):
    pass


class InvalidPayload(Exception):
    pass
