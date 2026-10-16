import json
import re
from datetime import date, datetime

import pytz
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...savings.models import SavingType
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ...transactions.tests.factories import SavingChangeFactory, SavingCloseFactory
from .. import views
from .factories import SavingWorthFactory

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
    SavingFactory(saving_type=fund, price=bought, fee=fee, date=date(1999, 1, 1))
    SavingCloseFactory(
        from_account=fund,
        to_account=AccountFactory(title="Bank"),
        price=sold,
        fee=0,
        date=date(1999, 6, 1),
    )
    SavingWorthFactory(
        saving_type=fund, price=0, date=datetime(1999, 12, 31, 12, tzinfo=pytz.utc)
    )
    return fund


def row_cells(content, title):
    row = re.search(rf"<tr>\s*<td[^>]*>{title}</td>(.*?)</tr>", content, re.S)
    return [c.strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row.group(1), re.S)]


def script_json(content, script_id):
    found = re.search(rf'<script id="{script_id}"[^>]*>(.*?)</script>', content, re.S)
    return json.loads(found.group(1))


def worth_in_1999(fund, price, month=12):
    return SavingWorthFactory(
        saving_type=fund,
        price=price,
        date=datetime(1999, month, 28, 12, tzinfo=pytz.utc),
    )


def switch_a_into_b(*, kind="funds", a_closed=None, switched=130000):
    """A bought 1 000,00, worth 1 300,00, all switched into B; A ends at 0, B at 1 400,00."""
    a = SavingTypeFactory(title="A", type=kind, closed=a_closed)
    b = SavingTypeFactory(title="B", type=kind)
    SavingFactory(saving_type=a, price=100000, fee=0, date=date(1999, 1, 1))
    worth_in_1999(a, 130000, month=5)
    SavingChangeFactory(
        from_account=a, to_account=b, price=switched, fee=0, date=date(1999, 6, 1)
    )
    worth_in_1999(a, 0)
    worth_in_1999(b, 140000)
    return a, b


def total_cells(content):
    """The Viso row of the funds table, one string per cell."""
    foot = re.search(r"<tfoot>(.*?)</tfoot>", content, re.S).group(1)
    return [c.strip() for c in re.findall(r"<th[^>]*>(.*?)</th>", foot, re.S)]


def view_queries(client, name, build, count):
    """Queries the view runs once `build(i)` has made `count` saving types."""
    while SavingType.objects.count() < count:
        build(SavingType.objects.count())
    with CaptureQueriesContext(connection) as ctx:
        client.get(reverse(name))
    return len(ctx)
