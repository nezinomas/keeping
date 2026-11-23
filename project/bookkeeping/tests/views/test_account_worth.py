import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ....accounts.tests.factories import AccountBalanceFactory
from ..factories import AccountWorthFactory
from ..helper import tab_table

pytestmark = pytest.mark.django_db


def _accounts(client):
    return tab_table(client, "bookkeeping:tab_overview", "Sąskaitos")


def _two_checks():
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=ZoneInfo("UTC")), price=2)
    AccountWorthFactory(date=datetime(1999, 2, 2, tzinfo=ZoneInfo("UTC")), price=555)


@pytest.mark.parametrize(
    "seed, tip, have",
    [
        pytest.param(_two_checks, "1999 m. vasario 2 d., 00:00", "5,55", id="checked"),
        pytest.param(
            AccountBalanceFactory, "Nėra įrašo apie sąskaitos lėšas", "0,20", id="none"
        ),
    ],
)
def test_accounts_row_tips_its_latest_check_and_reads_its_worth(
    client_logged, seed, tip, have
):
    seed()

    actual = _accounts(client_logged)

    # the name's tip, then Turiu: the row's sixth cell
    assert re.findall(
        r'<span class="tip right w100" tabindex="0" data-tip="([^"]*)"'
        r' aria-description="\1">Account1</span>\s*</td>'
        r"(?:\s*<td[^>]*>[^<]*</td>){4}\s*<td[^>]*>([^<]*)</td>",
        actual,
    ) == [(tip, have)]
