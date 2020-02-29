import re
import shlex

import requests

from lpipe.exceptions import GraphQLError, InvalidTaxonomyURI


def query_graphql(raw_query, endpoint):
    """Query a graphql API handle errors."""
    query = " ".join(shlex.split(raw_query, posix=False))
    r = requests.get(endpoint, params={"query": query})
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 400:
        response = r.json()
        assert "errors" in response
        raise GraphQLError("".join([e["message"] for e in response["errors"]]))
    else:
        raise requests.exceptions.RequestException(
            f"HTTP Status: {r.status_code}, Response Body: {r.text}"
        )


class TaxonomyURI:
    pattern = re.compile(
        r"taxonomy-v(?P<version>[0-9]+)/(?P<type>[a-z,\-]+)/(?P<id>[0-9]+)"
    )

    def __init__(self, version, type, id):
        self.version = version
        self.type = type
        self.id = id

    @staticmethod
    def from_str(raw):
        try:
            m = TaxonomyURI.pattern.search(raw)
            return TaxonomyURI(
                version=m.group("version"), type=m.group("type"), id=m.group("id")
            )
        except Exception as e:
            raise InvalidTaxonomyURI() from e

    @staticmethod
    def build(uri):
        """Given a URI (string or object), return a TaxonomyURI"""
        return uri if type(uri) is TaxonomyURI else TaxonomyURI.from_str(uri)

    @property
    def encoded(self):
        return f"taxonomy-v{self.version}/{self.type}/{self.id}"

    def __repr__(self):
        return self.encoded


class Company:
    """Barebones representation of a taxonomy company for this module only."""

    def __init__(self, uri, industry=None, products={}):
        self.uri = uri
        if industry:
            self.industry = industry
        else:
            self._industry = None
        self.products = products

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = TaxonomyURI.build(uri)

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, uri):
        self._industry = TaxonomyURI.build(uri)

    def __repr__(self):
        return str(self.uri.id)


class Brand:
    """Barebones representation of a taxonomy brand for this module only."""

    def __init__(self, uri, company=None, products={}):
        self.uri = uri
        if company:
            self.company = company
        else:
            self._company = None
        self.products = products

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = TaxonomyURI.build(uri)

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, uri):
        self._company = TaxonomyURI.build(uri)

    def __repr__(self):
        return str(self.uri.id)


class Product:
    """Barebones representation of a taxonomy product for this module only."""

    def __init__(self, uri, branded=None, product_type=None, company=None):
        self.uri = uri
        self.branded = branded

        if product_type:
            self.product_type = product_type
        else:
            self._product_type = None

        if company:
            self.company = company
        else:
            self._company = None

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = TaxonomyURI.build(uri)

    @property
    def product_type(self):
        return self._product_type

    @product_type.setter
    def product_type(self, uri):
        self._product_type = TaxonomyURI.build(uri)

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, uri):
        self._company = TaxonomyURI.build(uri)

    def __repr__(self):
        return str(self.uri.id)
