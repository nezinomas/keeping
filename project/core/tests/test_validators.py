import pytest
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from hypothesis import example, given
from hypothesis import strategies as st

from ..validators import title_characters_in, validate_title_slug


def _refusal(title: str) -> tuple[str, list[str]]:
    try:
        validate_title_slug(title)
    except ValidationError as error:
        return error.code, error.messages

    return "", []


@pytest.mark.parametrize(
    "title, code, messages",
    [
        pytest.param(
            "Pienas ½ l",
            "expanding_characters",
            ["Pavadinime negali būti „½“."],
            id="an_expanding_character",
        ),
        pytest.param(
            "ﬃ ½ ﬃ x",
            "expanding_characters",
            ["Pavadinime negali būti „ﬃ, ½“."],
            id="each_expanding_character_once_in_order",
        ),
        pytest.param(
            "€€€",
            "empty_slug",
            ["Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."],
            id="no_latin_letter_or_digit",
        ),
    ],
)
def test_title_slug_refuses(title, code, messages):
    assert _refusal(title) == (code, messages)


def test_title_slug_lets_no_expanding_character_through():
    expanding = []
    for code_point in range(0x20000):
        title = f"a{chr(code_point)}a"
        if len(slugify(title)) <= len(title):
            continue
        try:
            validate_title_slug(title)
        except ValidationError:
            continue
        expanding.append(chr(code_point))

    assert expanding == []


@st.composite
def plain_titles(draw):
    """Lithuanian and Latin letters, digits, spaces and `&-.`, with one letter or
    digit at least: no character slugify writes as several."""
    rest = st.text(alphabet="aząčęėįšųūžAZĄŽß09 &-.", max_size=20)

    return draw(rest) + draw(st.sampled_from("azĄž09")) + draw(rest)


@given(plain_titles())
@example("Būstas")
@example("Straße")
@example("ąčęėįšųūž")
@example("Druska & Cukrus")
def test_title_slug_accepts_titles_without_expanding_characters(title):
    assert _refusal(title) == ("", [])


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
