import pytest

from lpipe.taxonomy import InvalidTaxonomyURI, TaxonomyURI


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
            uri = TaxonomyURI.from_str("taxonomy-v/foobar/5678")

    def test_from_str_invalid_type(self):
        with pytest.raises(InvalidTaxonomyURI):
            uri = TaxonomyURI.from_str("taxonomy-v1/asdf1234/5678")

    def test_from_str_invalid_id(self):
        with pytest.raises(InvalidTaxonomyURI):
            uri = TaxonomyURI.from_str("taxonomy-v1/foobar/asdf")

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
