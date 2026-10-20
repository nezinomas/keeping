from django.template import engines
from django_cotton.compiler_regex import CottonCompiler

ITEMS = [
    {"label": "Sausis", "url": "/t/?month=1", "active": False},
    {"label": "Vasaris", "url": "/t/?month=2", "active": True},
]


def _render(source: str, context: dict) -> str:
    # only the cotton loader rewrites <c-…>, so a string runs its compiler by hand
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render(context)


def test_the_filter_line_draws_one_item_per_entry():
    content = _render(
        '<c-filter-line :items="items" target="#tab_content" />', {"items": ITEMS}
    )

    assert content.count("<button") == 2
    assert (
        '<button type="button" class="filter-line__item"'
        ' hx-get="/t/?month=1" hx-push-url="true" hx-target="#tab_content">'
        "Sausis</button>"
    ) in content
    assert (
        '<button type="button" class="filter-line__item" aria-current="true"'
        ' hx-get="/t/?month=2" hx-push-url="true" hx-target="#tab_content">'
        "Vasaris</button>"
    ) in content
