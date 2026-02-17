from datetime import date

import pytest

from ..converters import DateConverter, SignerConverter


@pytest.fixture(name="date_converter")
def fixture_date_converter():
    return DateConverter()


def test_converter_regex(date_converter):
    """Ensure the regex matches the expected Django URL pattern."""
    assert date_converter.regex == r"(\d{4}-\d{1,2}-\d{1,2})"


def test_to_python_valid_date_string(date_converter):
    """Test successful conversion from a URL string to a Python date object."""
    result = date_converter.to_python("2026-02-17")
    assert result == date(2026, 2, 17)


def test_to_python_invalid_date_string(date_converter):
    """Test that an improperly formatted string raises a ValueError."""
    with pytest.raises(ValueError):
        date_converter.to_python("02-17-2026")  # Wrong format


def test_to_url_valid_date(mocker, date_converter):
    """Test successful string formatting of a valid date object using pytest-mock."""
    # Create a mock object that simulates a datetime/date object
    mock_date = mocker.Mock()
    mock_date.strftime.return_value = "2026-02-17"

    result = date_converter.to_url(mock_date)

    # Verify strftime was called with the exact format required
    mock_date.strftime.assert_called_once_with("%Y-%m-%d")
    assert result == "2026-02-17"


def test_to_url_attribute_error(date_converter):
    """Test the fallback behavior when an object without a strftime method is passed."""
    # Passing an integer will trigger an AttributeError when .strftime() is called
    result = date_converter.to_url(12345)

    # Verify the hardcoded fallback date is returned
    assert result == "1974-1-1"


@pytest.fixture(name="signer_converter")
def fixture_signer_converter():
    """Provides a fresh instance of SignerConverter for each test."""
    return SignerConverter()


@pytest.fixture
def sample_token():
    """Provides a realistic token string that matches the regex constraints."""
    # 23 chars : 5 chars : 43 chars
    part1 = "a-valid-token-string-12"
    part2 = "abcde"
    part3 = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v"
    return f"{part1}:{part2}:{part3}"


def test_signer_converter_regex(signer_converter):
    """Ensure the regex matches the expected Django URL pattern for a signed token."""
    assert signer_converter.regex == r"([\w\-]{23,}:[\w\-]{5,}:[\w\-]{43})"


def test_to_python_returns_unmodified_value(signer_converter, sample_token):
    """Test that to_python returns the token exactly as received from the URL."""
    result = signer_converter.to_python(sample_token)
    assert result == sample_token


def test_to_url_returns_unmodified_token(signer_converter, sample_token):
    """Test that to_url returns the token string exactly as passed to the URL dispatcher."""
    result = signer_converter.to_url(sample_token)
    assert result == sample_token