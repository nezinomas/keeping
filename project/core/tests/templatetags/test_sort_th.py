import pytest

from ..utils import render_cotton


@pytest.mark.parametrize(
    "url, expected",
    [
        pytest.param("/t/", 'hx-get="/t/?order=title"', id="no_query"),
        pytest.param(
            "/t/?scope=all", 'hx-get="/t/?scope=all&amp;order=title"', id="query"
        ),
    ],
)
def test_a_sort_link_adds_its_order_to_the_urls_query(url, expected):
    content = render_cotton(
        '<c-sort-th key="title" active="share" :url="url" target="#t">T</c-sort-th>',
        url=url,
    )

    assert f'<a role="button" {expected} hx-target="#t">T</a>' in content


@pytest.mark.parametrize(
    "state, expected",
    [
        pytest.param('align="left"', '<th class="text-left">', id="left"),
        pytest.param(
            'column="total"', '<th class="month-table__total">', id="total_column"
        ),
        pytest.param('align="right"', "<th>", id="other_value"),
        pytest.param('class="x"', "<th>", id="class_passed"),
    ],
)
def test_a_sort_header_maps_its_state_to_a_class(state, expected):
    content = render_cotton(
        f'<c-sort-th key="title" active="share" url="/t/" {state}>T</c-sort-th>'
    )

    assert content.strip().startswith(expected)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("<c-sort-th>T</c-sort-th>", id="span"),
        # a given key draws the link, where a leaked url, target or active shows
        pytest.param('<c-sort-th key="title">T</c-sort-th>', id="link"),
    ],
)
def test_a_sort_header_draws_nothing_it_is_not_given(source):
    page = {
        "key": "Puslapio",
        "active": "title",
        "url": "/puslapio/",
        "target": "#puslapio",
        "align": "left",
        "column": "total",
    }

    assert render_cotton(source, **page) == render_cotton(source)
