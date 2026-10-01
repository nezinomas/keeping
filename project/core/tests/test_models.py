import pytest
from django.apps import apps
from django.core.exceptions import ValidationError

from ..models import TitleAbstract
from .factories import OwnedTitleDummyFactory, TitleDummyFactory

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


@pytest.mark.parametrize("title", ["...", "---", "___", "Мясо"])
def test_title_abstract_empty_slug(title):
    dummy = TitleDummyFactory.build(title=title)

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert exc.value.message_dict["title"] == [
        "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."
    ]


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


# ----------------------------------------------------------------------------
#                                                         slug shared by owner
# ----------------------------------------------------------------------------
def test_title_abstract_slug_taken_by_owner():
    existing = OwnedTitleDummyFactory(title="Būstas")
    dummy = OwnedTitleDummyFactory.build(owner=existing.owner, title="Bustas")

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert exc.value.message_dict["title"] == [
        "Pavadinimas per daug panašus į jau esantį „Būstas“."
    ]


def test_title_abstract_same_slug_two_owners():
    OwnedTitleDummyFactory(title="Būstas")
    dummy = OwnedTitleDummyFactory.build(owner=TitleDummyFactory(), title="Bustas")

    dummy.full_clean()


def test_title_abstract_slug_own_title_is_valid():
    dummy = OwnedTitleDummyFactory(title="Būstas")

    dummy.full_clean()


def test_title_abstract_slug_case_change_is_valid():
    dummy = OwnedTitleDummyFactory(title="Bustas")
    dummy.title = "BUSTAS"

    dummy.full_clean()


def test_title_abstract_identical_title_reported_once():
    existing = OwnedTitleDummyFactory(title="Bustas")
    dummy = OwnedTitleDummyFactory.build(owner=existing.owner, title="Bustas")

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert len(exc.value.messages) == 1


def test_title_abstract_identical_title_names_the_existing_one():
    existing = OwnedTitleDummyFactory(title="Būstas")
    dummy = OwnedTitleDummyFactory.build(owner=existing.owner, title="Būstas")

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert exc.value.message_dict["title"] == ["„Būstas“ jau yra."]


def test_title_abstract_without_owner_is_not_checked():
    TitleDummyFactory(title="Būstas")

    TitleDummyFactory.build(title="Bustas").full_clean()


@pytest.mark.parametrize(
    "model",
    [model for model in apps.get_models() if issubclass(model, TitleAbstract)],
    ids=lambda model: model.__name__,
)
def test_title_abstract_slug_column_holds_its_title(model):
    title = model._meta.get_field("title")
    slug = model._meta.get_field("slug")

    assert slug.max_length >= title.max_length
