import re

import pytest
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def _render(source: str, context: dict) -> str:
    # only the cotton loader rewrites <c-…>, so a string runs its compiler by hand
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render(context)


# a tab page's context holds its own `tab`, which must not reach a pill without one
PAGE = {"url": "/url/", "tab": "data"}
PILL = 'class="quick-add__pill" hx-get="/url/" hx-target="#mainModal">Naujas</button>'


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            '<c-quick-add.pill :url="url">Naujas</c-quick-add.pill>',
            f'<button type="button" {PILL}',
            id="no-tab",
        ),
        pytest.param(
            '<c-quick-add.pill :url="url" tab="types">Naujas</c-quick-add.pill>',
            f'<button type="button" x-show="tab === \'types\'" x-cloak {PILL}',
            id="tab",
        ),
    ],
)
def test_the_pill_loads_its_url_into_the_modal(source, expected):
    assert expected in _render(source, PAGE)


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            '<c-quick-add.link :url="url">Eiti</c-quick-add.link>',
            '<a class="quick-add__pill" href="/url/">Eiti</a>',
            id="no-tab",
        ),
        pytest.param(
            '<c-quick-add.link :url="url" tab="types">Eiti</c-quick-add.link>',
            "<a x-show=\"tab === 'types'\" x-cloak "
            'class="quick-add__pill" href="/url/">Eiti</a>',
            id="tab",
        ),
    ],
)
def test_the_link_is_an_anchor_with_the_pill_look(source, expected):
    content = _render(source, PAGE)

    assert expected in content
    assert "hx-get" not in content


def test_the_attrs_land_on_the_bar_root():
    content = _render('<c-quick-add id="x">slot</c-quick-add>', {})

    assert '<div class="quick-add" id="x">' in content


def test_the_slot_follows_the_count_inside_the_pills():
    content = _render(
        "<c-quick-add><i>slot</i></c-quick-add>", {"yday": 275, "ydays": 365}
    )

    assert content.index("275") < content.index('<div class="quick-add__pills">')
    assert '<div class="quick-add__pills"><i>slot</i></div>' in content


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            '<c-quick-add><c-slot name="sheet"><form></form></c-slot></c-quick-add>',
            "<form></form>",
            id="sheet",
        ),
        pytest.param("<c-quick-add>slot</c-quick-add>", "", id="no_sheet"),
    ],
)
def test_the_sheet_slot_sits_above_the_bar(source, expected):
    content = _render(source, {})
    above_the_bar = re.search(
        r'<div class="quick-add"[^>]*>(.*?)<div class="quick-add__bar">', content, re.S
    )

    assert above_the_bar.group(1).strip() == expected


def test_the_count_reads_the_day_of_the_year():
    content = _render("<c-day-of-year />", {"yday": 275, "ydays": 365})

    assert '<div class="day-of-year"><span>275 / <b>365</b></span></div>' in content
