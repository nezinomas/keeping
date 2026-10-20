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
