import contextlib
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
from .factories import SavingWorthFactory


def assert_(expected, actual):  # sourcery skip: raise-specific-error
    for saving_type, arr in expected.items():
        for _k, expected_val in expected[saving_type].items():
            try:
                actual_val = actual[saving_type][_k]
            except KeyError as e:
                raise Exception(f"No '{_k}' key in {actual[saving_type]}.") from e

            with contextlib.suppress(Exception):
                actual_val = round(float(actual_val), 2)

            msg = f"{saving_type}->{_k}. Expected={expected_val} Actual={actual_val}"

            assert expected_val == actual_val, msg


def filter_fixture(data, leave_keys):
    rm_keys = set(data.keys()) - set(leave_keys)

    for key in rm_keys:
        data.pop(key)


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
