import pytest
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from ..validators import title_characters_in, validate_title_slug


def test_title_slug_refuses_expanding_character():
    with pytest.raises(ValidationError) as exc:
        validate_title_slug("Pienas ½ l")

    assert exc.value.messages == ["Pavadinime negali būti „½“."]
    assert exc.value.code == "expanding_characters"


def test_title_slug_names_each_expanding_character_once_in_order():
    with pytest.raises(ValidationError) as exc:
        validate_title_slug("ﬃ ½ ﬃ x")

    assert exc.value.messages == ["Pavadinime negali būti „ﬃ, ½“."]


def test_title_slug_lets_no_expanding_character_through():
    expanding = []
    for code_point in range(0x20000):
        title = f"a{chr(code_point)}a"
        try:
            validate_title_slug(title)
        except ValidationError:
            continue
        if len(slugify(title)) > len(title):
            expanding.append(chr(code_point))

    assert expanding == []


@pytest.mark.parametrize("title", ["Būstas", "Straße", "ąčęėįšųūž", "Druska & Cukrus"])
def test_title_slug_accepts_titles_without_expanding_characters(title):
    validate_title_slug(title)


def test_title_slug_empty_slug_message_unchanged():
    with pytest.raises(ValidationError) as exc:
        validate_title_slug("€€€")

    assert exc.value.messages == [
        "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."
    ]


@pytest.mark.parametrize(
    "value, expect",
    [
        ("jonas+test@mail.lt", "jonastestmail.lt"),
        ("Būstas ½ ﬃ-x_y", "Būstas  -x_y"),
        ("@+@", ""),
    ],
)
def test_title_characters_in(value, expect):
    assert title_characters_in(value) == expect
