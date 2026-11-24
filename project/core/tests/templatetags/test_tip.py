from ..utils import render_cotton

# a page's own values under a tip's names, none of which the tip is given
PAGE = {
    "side": "page",
    "text": "page",
    "class": "page",
    "wide": True,
    "label": "page",
    "description": "page",
    "focusable": False,
}


def test_a_tip_draws_nothing_it_is_not_given():
    content = render_cotton("<c-tip>slot</c-tip>", **PAGE)

    assert content == '<span class="tip " tabindex="0" data-tip="">slot</span>'
