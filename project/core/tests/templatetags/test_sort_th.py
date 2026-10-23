import pytest
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def _render(source: str, context: dict) -> str:
    # only the cotton loader rewrites <c-…>, so a string runs its compiler by hand
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render(context)


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
    content = _render(
        '<c-sort-th key="title" active="share" :url="url" target="#t">T</c-sort-th>',
        {"url": url},
    )

    assert f'<a role="button" {expected} hx-target="#t">T</a>' in content


@pytest.mark.parametrize(
    "state, expected",
    [
        pytest.param('align="left"', '<th class="text-left">', id="left"),
        pytest.param(
            'column="title"', '<th class="text-left title-col">', id="title_column"
        ),
        pytest.param(
            'column="total"', '<th class="month-table__total">', id="total_column"
        ),
        pytest.param('align="right"', "<th>", id="other_value"),
        pytest.param('class="x"', "<th>", id="class_passed"),
    ],
)
def test_a_sort_header_maps_its_state_to_a_class(state, expected):
    content = _render(
        f'<c-sort-th key="title" active="share" url="/t/" {state}>T</c-sort-th>', {}
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
        "column": "title",
    }

    assert _render(source, page) == _render(source, {})
