from ..utils import render_cotton

ITEMS = [
    {"label": "Sausis", "url": "/t/?month=1", "active": False},
    {"label": "Vasaris", "url": "/t/?month=2", "active": True},
]


def test_the_filter_line_draws_one_item_per_entry():
    content = render_cotton(
        '<c-filter-line :items="items" target="#tab_content" />', items=ITEMS
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
