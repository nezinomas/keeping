import pytest
from datetime import date

from ..converters import DateConverter

# --- Tests ---

@pytest.fixture(name="converter")
def fixture_converter():
    return DateConverter()


def test_converter_regex(converter):
    """Ensure the regex matches the expected Django URL pattern."""
    assert converter.regex == r"(\d{4}-\d{1,2}-\d{1,2})"


def test_to_python_valid_date_string(converter):
    """Test successful conversion from a URL string to a Python date object."""
    result = converter.to_python("2026-02-17")
    assert result == date(2026, 2, 17)


def test_to_python_invalid_date_string(converter):
    """Test that an improperly formatted string raises a ValueError."""
    with pytest.raises(ValueError):
        converter.to_python("02-17-2026")  # Wrong format


def test_to_url_valid_date(mocker, converter):
    """Test successful string formatting of a valid date object using pytest-mock."""
    # Create a mock object that simulates a datetime/date object
    mock_date = mocker.Mock()
    mock_date.strftime.return_value = "2026-02-17"

    result = converter.to_url(mock_date)

    # Verify strftime was called with the exact format required
    mock_date.strftime.assert_called_once_with("%Y-%m-%d")
    assert result == "2026-02-17"


def test_to_url_attribute_error(converter):
    """Test the fallback behavior when an object without a strftime method is passed."""
    # Passing an integer will trigger an AttributeError when .strftime() is called
    result = converter.to_url(12345)

    # Verify the hardcoded fallback date is returned
    assert result == "1974-1-1"