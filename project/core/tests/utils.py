import re

from django.db import connection
from django.test.utils import CaptureQueriesContext

PICKER_SCRIPT = r'<script[^>]*src="[^"]*/js/([a-z]+-picker\.js)"'
STICKY_HEADERS = r'<script nonce="[^"]*" src="/static/js/sticky-table-headers.js">'


def edit_row_opening(url):
    """The start tag of a list row whose double-click opens `url` in the modal."""
    return f'<tr hx-get="{url}" hx-trigger="dblclick" hx-target="#mainModal"'


ROW = re.compile(
    r'<tr hx-get="([^"]*)" hx-trigger="dblclick" hx-target="#mainModal"[^>]*>'
    r"(.*?)</tr>",
    re.DOTALL,
)
ROW_BUTTON = re.compile(
    r'<td class="(edit-col|delete-col)">\s*<a role="button" hx-get="([^"]*)"'
)


def row_forms(content):
    """(the url a double click opens, [(column, url) of each button]) of each row."""
    return [(url, ROW_BUTTON.findall(cells)) for url, cells in ROW.findall(content)]


def clean_content(rendered):
    return str(rendered).replace("\n", "").replace("\t", "").replace("  ", "")


def tab_fragment(client, url):
    """A tab's fragment, as htmx asks for it."""
    return client.get(url, headers={"HX-Request": "true"}).content.decode()


def form_posts_to(content, form_id, url):
    form = rf'<form method="POST" id="{form_id}"[^>]* hx-post="{re.escape(url)}"'
    return bool(re.search(form, content))


def nav_tabs(content):
    """(name, url) of each tab the subnav offers."""
    return re.findall(r'<button\s+id="tab-(\w+)"[^>]*hx-get="([^"]*)"', content)


def quick_add_pills(content):
    """(tag, the tab it waits for or "", its url attribute, label) of each pill."""
    return re.findall(
        r"<(a|button)(?:[^>]*x-show=\"tab === '(\w+)'\" x-cloak)?[^>]*"
        r' class="quick-add__pill" ((?:href|hx-get)="[^"]*")[^>]*>([^<]*)</\1>',
        content,
    )


FOLD_PART = re.compile(
    r'<table class="main striped hover sticky-table"(?P<attrs>[^>]*)>'
    r"(?P<body>.*?)</table>"
    r'|<div class="alert">\s*(?P<notice>[^<]*?)\s*</div>'
    r'|(?P<scope><div x-data="\{ shown: false \}">\s*)?'
    r'<nav class="filter-line"(?P<nav_attrs>[^>]*)>(?P<nav>.*?)</nav>',
    re.DOTALL,
)
FOLDED = ' x-show="shown" x-cloak'
FOLD_BUTTON = "the fold's button"
OTHER_FILTER_LINE = "another filter line"


def closed_fold(content, label):
    """The tab's tables, notice and filter lines, in page order; `label` is the
    button that unfolds the closed owners."""
    button = re.compile(
        r'\s*<button type="button" class="filter-line__item" @click="shown = ! shown"'
        r""" :aria-current="shown \? 'true' : null">"""
        + re.escape(label)
        + r"</button>\s*"
    )
    parts = []
    for part in FOLD_PART.finditer(content):
        if part["notice"] is not None:
            parts.append(part["notice"])
        elif part["nav"] is not None:
            scoped = part["scope"] and not part["nav_attrs"]
            parts.append(
                FOLD_BUTTON
                if scoped and button.fullmatch(part["nav"])
                else OTHER_FILTER_LINE
            )
        else:
            parts.append(
                (
                    part["attrs"],
                    re.findall(r'<th class="([^"]*)">([^<]*)</th>', part["body"]),
                    re.findall(
                        r'<tr hx-get="[^"]*" hx-trigger="dblclick"'
                        r' hx-target="#mainModal">\s*'
                        r'<td class="text-left main__name">(.*?)</td>',
                        part["body"],
                    ),
                )
            )
    return parts


# an empty Card's figure is its bare dash; stop at the next label, never pair Cards
IN_CARD = r"(?:(?!trend-card__label).)*?"
CARD = re.compile(
    rf'<div class="trend-card__label">([^<]*)</div>{IN_CARD}'
    r'(?:<span class="trend-card__figure"[^>]*>|trend-card__value--empty">)'
    rf"([^<]*){IN_CARD}"
    r'<div class="trend-card__note">([^<]*)</div>',
    re.S,
)
TOOLTIP = re.compile(r'<span class="trend-card__explanation" role="tooltip"><p>([^<]*)')
EDIT_BUTTON = re.compile(
    r'<button type="button" class="trend-card__edit" hx-get="([^"]*)"'
    r'[^>]*hx-target="#mainModal"[^>]*><i class="bi bi-pencil"'
)
CARD_VALUE = re.compile(
    r'<div class="trend-card__label">([^<]*)</div>\s*'
    r'(<div class="trend-card__value[^>]*>.*?</div>)',
    re.S,
)


def stat_cards(content):
    """(label, figure, note) of each Card."""
    return CARD.findall(content)


def stat_card_edit_urls(content):
    """The url each Card's pencil opens in the modal."""
    return EDIT_BUTTON.findall(content)


def stat_card_values(content):
    """Each Card's value element (arrow, figure, meta stack), by its label."""
    return dict(CARD_VALUE.findall(content))


def stat_card_tooltips(content):
    return TOOLTIP.findall(content)


def count_queries(run, starting_with=""):
    with CaptureQueriesContext(connection) as queries:
        run()
    return sum(query["sql"].startswith(starting_with) for query in queries)


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
