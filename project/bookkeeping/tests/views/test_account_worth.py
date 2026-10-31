import re
from datetime import datetime

import pytest
import pytz
from django.urls import reverse

from ....accounts.tests.factories import AccountBalanceFactory
from ..factories import AccountWorthFactory

pytestmark = pytest.mark.django_db


def test_view(client_logged):
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    AccountWorthFactory(date=datetime(1999, 2, 2, tzinfo=pytz.utc), price=555)

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert 'data-tip="1999 m. vasario 2 d., 00:00">Account1</span>' in actual
    assert re.search(
        r'<td class="left-thick-border" data-cell="[^"]*">5,55</td>', actual
    )


def test_view_last_check_empty(client_logged):
    AccountBalanceFactory()

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert 'data-tip="Nėra įrašo apie sąskaitos lėšas"' in actual
    assert '<td class="left-thick-border" data-cell="">0,20</td>' in actual
