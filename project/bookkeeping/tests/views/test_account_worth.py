import re
from datetime import datetime

import pytest
import pytz

from ....accounts.tests.factories import AccountBalanceFactory
from ..factories import AccountWorthFactory
from ..helper import tab_table

pytestmark = pytest.mark.django_db


def _accounts(client):
    return tab_table(client, "bookkeeping:tab_overview", "Sąskaitos")


def test_accounts_table_shows_the_latest_check_and_its_worth(client_logged):
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    AccountWorthFactory(date=datetime(1999, 2, 2, tzinfo=pytz.utc), price=555)

    actual = _accounts(client_logged)

    assert 'data-tip="1999 m. vasario 2 d., 00:00">Account1</span>' in actual
    assert re.search(
        r'<td class="left-thick-border" data-cell="[^"]*">5,55</td>', actual
    )


def test_accounts_table_without_a_check_says_so(client_logged):
    AccountBalanceFactory()

    actual = _accounts(client_logged)

    assert re.search(
        r'<span class="tip[^"]*" data-tip="Nėra įrašo apie sąskaitos lėšas">', actual
    )
    assert '<td class="left-thick-border" data-cell="">0,20</td>' in actual
