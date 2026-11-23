import re

import pytest

from ..utils import render_cotton

# a tab page's context holds its own `tab`, which must not reach a pill without one
PAGE = {"url": "/url/", "tab": "data"}


# the pill loads its url into the modal, the link is an anchor with the pill's look;
# each shows only on the tab it names
@pytest.mark.parametrize(
    "tab, shown",
    [("", ""), (' tab="types"', "x-show=\"tab === 'types'\" x-cloak ")],
    ids=["no-tab", "tab"],
)
@pytest.mark.parametrize(
    "component, label, element",
    [
        pytest.param(
            "pill",
            "Naujas",
            '<button type="button" {shown}class="quick-add__pill" hx-get="/url/"'
            ' hx-target="#mainModal">Naujas</button>',
            id="pill",
        ),
        pytest.param(
            "link",
            "Eiti",
            '<a {shown}class="quick-add__pill" href="/url/">Eiti</a>',
            id="link",
        ),
    ],
)
def test_a_quick_add_pill_or_link_draws_its_one_element(
    component, label, element, tab, shown
):
    source = (
        f'<c-quick-add.{component} :url="url"{tab}>{label}</c-quick-add.{component}>'
    )

    content = render_cotton(source, **PAGE)

    assert re.findall(r"<(?:button|a)\b.*?</(?:button|a)>", content, re.S) == [
        element.format(shown=shown)
    ]


def test_the_attrs_land_on_the_bar_root():
    content = render_cotton('<c-quick-add id="x">slot</c-quick-add>')

    assert '<div class="quick-add" id="x">' in content


def test_the_slot_follows_the_count_inside_the_pills():
    content = render_cotton(
        "<c-quick-add><i>slot</i></c-quick-add>", yday=275, ydays=365
    )

    assert content.index('<div class="day-of-year">') < content.index(
        '<div class="quick-add__pills">'
    )
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
    content = render_cotton(source)
    above_the_bar = re.search(
        r'<div class="quick-add"[^>]*>(.*?)<div class="quick-add__bar">', content, re.S
    )

    assert above_the_bar.group(1).strip() == expected


def test_the_count_reads_the_day_of_the_year():
    content = render_cotton("<c-day-of-year />", yday=275, ydays=365)

    assert '<div class="day-of-year"><span>275 / <b>365</b></span></div>' in content
