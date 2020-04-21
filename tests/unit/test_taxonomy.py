import pytest

from lpipe.exceptions import InvalidTaxonomyURI
from lpipe.taxonomy import Brand, Company, Product, TaxonomyURI


class TestTaxonomyURI:
    def test_init(self):
        uri = TaxonomyURI(1234, "foobar", 5678)
        assert uri.version == 1234
        assert uri.type == "foobar"
        assert uri.id == 5678

    def test_from_str(self):
        uri = TaxonomyURI.from_str("taxonomy-v1234/foobar/5678")
        assert uri.version == "1234"
        assert uri.type == "foobar"
        assert uri.id == "5678"

    def test_from_str_invalid_version(self):
        with pytest.raises(InvalidTaxonomyURI):
            TaxonomyURI.from_str("taxonomy-v/foobar/5678")

    def test_from_str_invalid_type(self):
        with pytest.raises(InvalidTaxonomyURI):
            TaxonomyURI.from_str("taxonomy-v1/asdf1234/5678")

    def test_from_str_invalid_id(self):
        with pytest.raises(InvalidTaxonomyURI):
            TaxonomyURI.from_str("taxonomy-v1/foobar/asdf")

    def test_build(self):
        uri = TaxonomyURI.build("taxonomy-v1234/foobar/5678")
        assert uri.version == "1234"
        assert uri.type == "foobar"
        assert uri.id == "5678"

    def test_build_already_a_uri(self):
        uri = TaxonomyURI.build(TaxonomyURI(1234, "foobar", 5678))
        assert uri.version == 1234
        assert uri.type == "foobar"
        assert uri.id == 5678

    def test_encoded(self):
        uri = TaxonomyURI(1234, "foobar", 5678)
        assert isinstance(uri.encoded, str)


def test_company():
    company = Company("taxonomy-v1234/company/5678")
    assert company.uri.type == "company"


def test_brand():
    brand = Brand("taxonomy-v1234/brand/5678")
    assert brand.uri.type == "brand"


def test_product():
    product = Product("taxonomy-v1234/product/5678")
    assert product.uri.type == "product"
