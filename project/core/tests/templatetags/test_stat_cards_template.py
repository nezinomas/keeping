from django.template.loader import render_to_string

from ...lib.stat_card import EmptyStatCard, StatCard


def _render(card) -> str:
    return render_to_string("cotton/stat_cards.html", {"cards": [card]})


def test_a_figure_carries_its_full_value_for_when_it_is_cut_short():
    content = _render(StatCard(title="Largest type", value="Atlyginimas"))

    assert (
        '<span class="trend-card__figure" title="Atlyginimas">Atlyginimas</span>'
        in content
    )


def test_an_empty_card_has_no_figure_to_cut():
    content = _render(EmptyStatCard("Largest type"))

    assert "trend-card__figure" not in content
