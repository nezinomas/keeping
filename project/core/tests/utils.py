import re

from django.db import connection
from django.test.utils import CaptureQueriesContext

PICKER_SCRIPT = r'<script[^>]*src="[^"]*/js/([a-z]+-picker\.js)"'


def clean_content(rendered):
    return str(rendered).replace("\n", "").replace("\t", "").replace("  ", "")


def quick_add_pills(content):
    """(tag, the tab it waits for or "", its url attribute, label) of each pill."""
    return re.findall(
        r"<(a|button)(?:[^>]*x-show=\"tab === '(\w+)'\" x-cloak)?[^>]*"
        r' class="quick-add__pill" ((?:href|hx-get)="[^"]*")[^>]*>([^<]*)</\1>',
        content,
    )


# an empty Card has no figure: stop at the next label, never pair across Cards
IN_CARD = r"(?:(?!trend-card__label).)*?"
CARD = re.compile(
    rf'<div class="trend-card__label">([^<]*)</div>{IN_CARD}'
    rf'<span class="trend-card__figure"[^>]*>([^<]*)</span>{IN_CARD}'
    r'<div class="trend-card__note">([^<]*)</div>',
    re.S,
)
TOOLTIP = re.compile(r'<span class="trend-card__explanation" role="tooltip"><p>([^<]*)')


def stat_cards(content):
    """(label, figure, note) of each Card."""
    return CARD.findall(content)


def stat_card_tooltips(content):
    return TOOLTIP.findall(content)


def count_queries(run):
    with CaptureQueriesContext(connection) as queries:
        run()
    return len(queries)


def setup_view(view, request, *args, **kwargs):
    """`as_view()` without dispatch: the view instance, to test its methods."""
    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


def view_for(rf, user, view_class, path="/", **kwargs):
    request = rf.get(path)
    request.user = user
    return setup_view(view_class(), request, **kwargs)
