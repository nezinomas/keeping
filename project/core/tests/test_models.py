import pytest
from django.core.exceptions import ValidationError
from django.db import models

from .factories import TitleDummyFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "title",
    [
        "Car Insurance",  # Standard with space
        "abc",  # Exactly 3 characters (Min boundary)
        "a" * 100,  # Exactly 100 characters (Max boundary)
        "Lietuviškas įrašas",  # Unicode/Lithuanian characters
        "Plan-A",  # Hyphens allowed
        "Test_123",  # Underscores and numbers allowed
        "Test.Other",  # Dot allowed
    ],
)
def test_title_abstract_valid(title):
    """Proves the Regex and length constraints accept valid data."""
    dummy = TitleDummyFactory(title=title)

    # If it is valid, full_clean() will execute silently without errors
    dummy.full_clean()


@pytest.mark.parametrize(
    "title",
    [
        "a",
        "ab",
    ],
)
def test_title_abstract_too_short(title):
    """Proves MinLengthValidator(3) blocks short strings."""
    dummy = TitleDummyFactory(title=title)

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert "title" in exc.value.message_dict


def test_title_abstract_too_long():
    """Proves max_length=100 blocks excessively long strings."""
    dummy = TitleDummyFactory(title="a" * 101)

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert "title" in exc.value.message_dict


@pytest.mark.parametrize(
    "title",
    [
        "Drop * table",
        "My@Plan",
        "<script>alert('x')</script>",
        "Insurance/Home",
        "Newline\nBreak",
    ],
)
def test_title_abstract_invalid_characters(title):
    dummy = TitleDummyFactory.build(title=title)

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert "title" in exc.value.message_dict


@pytest.mark.parametrize(
    "title",
    [
        "",
        None,
    ],
)
def test_title_abstract_blank_or_null(title):
    dummy = TitleDummyFactory.build(title=title)

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert "title" in exc.value.message_dict
