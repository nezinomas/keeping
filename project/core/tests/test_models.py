import pytest
from django.apps import apps
from django.core.exceptions import ValidationError

from ..models import TitleAbstract
from .factories import OwnedTitleDummyFactory, TitleDummyFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "title",
    [
        "Car Insurance",
        "abc",
        "a" * 100,
        "Lietuviškas įrašas",
        "Plan-A",
        "Test_123",
        "Test.Other",
    ],
)
def test_title_abstract_valid(title):
    TitleDummyFactory(title=title).full_clean()


@pytest.mark.parametrize(
    "title",
    [
        pytest.param("a", id="too_short_1"),
        pytest.param("ab", id="too_short_2"),
        pytest.param("a" * 101, id="too_long"),
        pytest.param("Drop * table", id="invalid_space_star"),
        pytest.param("My@Plan", id="invalid_at"),
        pytest.param("<script>alert('x')</script>", id="invalid_tags"),
        pytest.param("Insurance/Home", id="invalid_slash"),
        pytest.param("Newline\nBreak", id="invalid_newline"),
        pytest.param("", id="blank"),
        pytest.param(None, id="null"),
    ],
)
def test_title_abstract_invalid(title):
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


def test_title_abstract_identical_title_names_the_existing_one():
    existing = OwnedTitleDummyFactory(title="Būstas")
    dummy = OwnedTitleDummyFactory.build(owner=existing.owner, title="Būstas")

    with pytest.raises(ValidationError) as exc:
        dummy.full_clean()

    assert exc.value.message_dict == {"title": ["„Būstas“ jau yra."]}


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
