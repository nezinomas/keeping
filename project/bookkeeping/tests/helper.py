import json
import re
from contextlib import contextmanager
from datetime import date
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...core.tests.utils import tab_fragment
from ...savings.models import SavingType
from ...savings.tests.factories import SavingTypeFactory
from ...transactions.tests.factories import SavingChangeFactory
from .. import balance_sources, views
from .signals.helpers import buy, sell, worth

WORTH_VIEWS = (views.AccountsWorthNew, views.SavingsWorthNew, views.PensionsWorthNew)


def worth_form(form_class, user, *, today, now, **kwargs):
    funds = {view.form_class: view.category_service_class for view in WORTH_VIEWS}
    return form_class(
        user=user,
        today=today,
        now=now,
        funds=funds[form_class](user).items(),
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


def script_json(content, script_id):
    found = re.search(rf'<script id="{script_id}"[^>]*>(.*?)</script>', content, re.S)
    assert found, f"no <script id={script_id}>"
    return json.loads(found.group(1))


def switch_a_into_b(*, kind="funds", a_closed=None, switched=130000):
    """A bought 1 000,00, worth 1 300,00, all switched into B; A ends at 0, B at 1 400,00."""
    a = SavingTypeFactory(title="A", type=kind, closed=a_closed)
    b = SavingTypeFactory(title="B", type=kind)
    buy(a, 100000)
    worth(a, 130000, month=5, day=28)
    SavingChangeFactory(
        from_account=a, to_account=b, price=switched, fee=0, date=date(1999, 6, 1)
    )
    worth(a, 0)
    worth(b, 140000)
    return a, b


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


def total_cells(table):
    """The cells of `table`'s foot rows, one string each."""
    foot = re.search(r"<tfoot>(.*?)</tfoot>", table, re.S).group(1)
    return [c.strip() for c in re.findall(r"<th[^>]*>(.*?)</th>", foot, re.S)]


@contextmanager
def quiet_syncs():
    """Saves inside the block sync no balance."""
    with (
        patch.object(balance_sources, "sync_accounts"),
        patch.object(balance_sources, "sync_savings"),
        patch.object(balance_sources, "sync_pensions"),
    ):
        yield


@contextmanager
def quiet_build(user):
    """Builds rows without the per-save balance syncs, then syncs each balance once.

    Build balance rows after the block: the closing syncs overwrite any built inside.
    """
    syncs = (
        balance_sources.sync_accounts,
        balance_sources.sync_savings,
        balance_sources.sync_pensions,
    )
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
