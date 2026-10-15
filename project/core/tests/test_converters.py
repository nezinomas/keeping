from datetime import date

import pytest

from ..converters import DateConverter, SignerConverter


@pytest.fixture(name="date_converter")
def fixture_date_converter():
    return DateConverter()


def test_converter_regex(date_converter):
    assert date_converter.regex == r"(\d{4}-\d{1,2}-\d{1,2})"


def test_to_python_valid_date_string(date_converter):
    result = date_converter.to_python("2026-02-17")
    assert result == date(2026, 2, 17)


def test_to_python_invalid_date_string(date_converter):
    with pytest.raises(ValueError):
        date_converter.to_python("02-17-2026")


def test_to_url_valid_date(date_converter):
    assert date_converter.to_url(date(2026, 2, 7)) == "2026-02-07"


def test_to_url_not_a_date_raises(date_converter):
    with pytest.raises(ValueError):
        date_converter.to_url(12345)


@pytest.fixture(name="signer_converter")
def fixture_signer_converter():
    """Provides a fresh instance of SignerConverter for each test."""
    return SignerConverter()


@pytest.fixture
def sample_token():
    # 23 chars : 5 chars : 43 chars
    part1 = "a-valid-token-string-12"
    part2 = "abcde"
    part3 = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v"
    return f"{part1}:{part2}:{part3}"


def test_signer_converter_regex(signer_converter):
    assert signer_converter.regex == r"([\w\-]{23,}:[\w\-]{5,}:[\w\-]{43})"


def test_to_python_returns_unmodified_value(signer_converter, sample_token):
    result = signer_converter.to_python(sample_token)
    assert result == sample_token


def test_to_url_returns_unmodified_token(signer_converter, sample_token):
    result = signer_converter.to_url(sample_token)
    assert result == sample_token
