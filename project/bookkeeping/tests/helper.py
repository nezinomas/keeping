import contextlib
import re
from datetime import date, datetime

import pytz

from ...accounts.tests.factories import AccountFactory
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ...transactions.tests.factories import SavingCloseFactory
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
