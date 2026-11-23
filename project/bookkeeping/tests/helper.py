import json
import re
from contextlib import contextmanager
from datetime import date
from unittest.mock import DEFAULT, patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...core.tests.utils import stat_cards, tab_fragment
from ...savings.models import SavingType
from ...savings.tests.factories import SavingTypeFactory
from ...transactions.tests.factories import SavingChangeFactory
from .. import balance_sources, views
from .signals.helpers import buy, sell, worth

# the Fondai tab's two tables and the kind of fund each lists
KINDS = [
    pytest.param("Fondai", "funds", id="funds"),
    pytest.param("Pensijos", "pensions", id="pensions"),
]

WORTH_VIEWS = (views.AccountsWorthNew, views.SavingsWorthNew, views.PensionsWorthNew)


def worth_form(form_class, user, *, today, now, **kwargs):
    owners = {view.form_class: view.owner_service_class for view in WORTH_VIEWS}
    return form_class(
        user=user,
        today=today,
        now=now,
        owners=owners[form_class](user).items(),
        **kwargs,
    )


def post_data(rows):
    data = {"form-TOTAL_FORMS": len(rows), "form-INITIAL_FORMS": 0}
    for number, row in enumerate(rows):
        data |= {f"form-{number}-{name}": value for name, value in row.items()}
    return data


def fund_with_a_sell(title, bought, sold, *, fee=0, kind="funds", closed=None):
    """Bought in 1999, sold in part or whole that June, worth 0 at the year end."""
    fund = SavingTypeFactory(title=title, type=kind, closed=closed)
    buy(fund, bought, fee=fee)
    sell(fund, sold)
    worth(fund, 0)
    return fund


def stale_fund(title="Stale", kind="funds"):
    """Worth 1 000,00 on 1 March, then 400,00 of it sold in June: the worth is stale."""
    fund = SavingTypeFactory(title=title, type=kind)
    buy(fund, 100000)
    worth(fund, 100000, month=3, day=1)
    sell(fund, 40000)
    return fund


def closed_every_other(i):
    """The close year of the i-th type of a guard that mixes closed and open ones."""
    return 1999 if i % 2 else None


def row_tags(content, title):
    """(attributes, text) of each `<td>` in the row titled `title`."""
    row = re.search(rf"<tr>\s*<td[^>]*>{title}</td>(.*?)</tr>", content, re.S)
    return [
        (attrs, text.strip())
        for attrs, text in re.findall(r"<td([^>]*)>(.*?)</td>", row.group(1), re.S)
    ]


def row_cells(content, title):
    return [text for _attrs, text in row_tags(content, title)]


CARD_STATE = re.compile(r'class="trend-card__value trend-card__value--(\w+)"')
CARD_UNIT = re.compile(r'<span class="trend-card__unit">([^<]*)</span>')


def tab_cards(content):
    """(label, figure with its unit, note, state) of each Card in the row that opens
    the tab."""
    row = content.partition('<div class="stat-cards">')[2].partition("<section")[0]
    return [
        (
            label,
            figure + "".join(CARD_UNIT.findall(card)),
            note,
            CARD_STATE.search(card).group(1),
        )
        for card in row.split('<div class="trend-card">')[1:]
        for label, figure, note in stat_cards(card)
    ]


def cell_texts(table):
    """Each row's cells as text, tags and spacing gone: head, body and foot."""
    return [
        [
            " ".join(re.sub(r"<[^>]+>", " ", cell).split())
            for cell in re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", row, re.S)
        ]
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, re.S)
    ]


def script_json(content, script_id):
    found = re.search(rf'<script id="{script_id}"[^>]*>(.*?)</script>', content, re.S)
    assert found, f"no <script id={script_id}>"
    return json.loads(found.group(1))


def switch_a_into_b(
    *, kind="funds", checked=date(1999, 3, 1), on=date(1999, 6, 1), a_zeroed=False
):
    """A bought for 1 000,00 in 1999, worth 1 300,00 on `checked`, switched whole to B
    on `on`; B worth 1 400,00 at the end of that year, and A 0 at 1999's when
    `a_zeroed`."""
    a = SavingTypeFactory(title="A", type=kind)
    b = SavingTypeFactory(title="B", type=kind)
    buy(a, 100000)
    worth(a, 130000, month=checked.month, day=checked.day, year=checked.year)
    SavingChangeFactory(from_account=a, to_account=b, price=130000, fee=0, date=on)
    if a_zeroed:
        worth(a, 0)
    worth(b, 140000, year=on.year)
    return a, b


FIGURE = ' class="main__figure"'
# a figure by its hook, whatever class sits beside it (Q194)
FIGURE_HOOK = ' class="main__figure(?: [^"]*)?"'
# a figure that starts a column group (sass.md *Tables*, *Column groups*)
GROUP_FIGURE = ' class="main__figure main__group-start"'
# a Panel's title, beside the control it may hold, and a table's class inside its
# scroll box
PANEL_TITLE = (
    r'<h2 class="panel__title">([^<]*?)\s*'
    r'(?:<span class="panel__control">[\s\S]*?</button>\s*</span>\s*)?</h2>\s*'
)
BOXED_TABLE = r'<div class="table-responsive">\s*<table class="([^"]*)"'


def table_titled(content, title):
    """The one table with a `<th>` reading `title`: a tab draws several."""
    tables = re.findall(r"<table\b.*?</table>", content, re.S)
    titled = [table for table in tables if re.search(rf">\s*{title}\s*</th>", table)]
    assert len(titled) == 1, f"{len(titled)} tables titled {title}"
    return titled[0]


def tab_table(client, url_name, title):
    """The table titled `title` on the tab at `url_name`, as its reload draws it."""
    return table_titled(tab_fragment(client, reverse(url_name)), title)


def row_titles(table):
    return re.findall(r"<tr>\s*<td[^>]*>([^<]*)</td>", table)


FUNDS_TAB = "bookkeeping:tab_funds"


def funds_table(client, title="Fondai"):
    """The Fondai tab's table titled `title`: Fondai or Pensijos."""
    return tab_table(client, FUNDS_TAB, title)


def signed_cells(cells):
    """(text, its data-sign or "") of each of the (attributes, text) `cells`."""
    return [
        (text, (re.findall(r'data-sign="(\w+)"', attrs) or [""])[0])
        for attrs, text in cells
    ]


def total_tags(table):
    """(attributes, text) of each cell of `table`'s foot rows."""
    foot = re.search(r"<tfoot>(.*?)</tfoot>", table, re.S).group(1)
    return [
        (attrs, text.strip())
        for attrs, text in re.findall(r"<t[hd]([^>]*)>(.*?)</t[hd]>", foot, re.S)
    ]


def total_cells(table):
    """The cells of `table`'s foot rows, one string each."""
    return [text for _attrs, text in total_tags(table)]


def _syncs() -> dict:
    """Each balance sync, by its name in `balance_sources`."""
    return {
        "sync_accounts": balance_sources.sync_accounts,
        "sync_savings": balance_sources.sync_savings,
        "sync_pensions": balance_sources.sync_pensions,
    }


@contextmanager
def quiet_syncs():
    """Saves inside the block sync no balance."""
    with patch.multiple(balance_sources, **dict.fromkeys(_syncs(), DEFAULT)):
        yield


@contextmanager
def quiet_build(user):
    """Builds rows without the per-save balance syncs, then syncs each balance once.

    Build balance rows after the block: the closing syncs overwrite any built inside.
    """
    syncs = _syncs().values()
    with quiet_syncs():
        yield
    for sync in syncs:
        sync(user)


def view_queries(client, user, name, build, count):
    """Queries the view runs once `build(i)` has made `count` saving types."""
    with quiet_build(user):
        while SavingType.objects.count() < count:
            build(SavingType.objects.count())
    with CaptureQueriesContext(connection) as ctx:
        client.get(reverse(name))
    return len(ctx)
