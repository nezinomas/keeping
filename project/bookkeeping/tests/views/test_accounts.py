import re
from datetime import datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ....accounts.tests.factories import AccountFactory
from ....incomes.tests.factories import IncomeFactory
from ....savings.tests.factories import SavingFactory
from ... import views
from .. import factories

pytestmark = pytest.mark.django_db


def test_func():
    view = resolve("/bookkeeping/accounts/")

    assert views.Accounts == view.func.view_class


def test_200(client_logged):
    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_302(client):
    url = reverse("bookkeeping:accounts")
    response = client.get(url)

    assert response.status_code == 302


def test_latest_check(client_logged):
    factories.AccountWorthFactory()
    factories.AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)
    items = response.context["items"]

    assert items[0].latest_check == datetime(1999, 1, 1, 1, 3, 4, tzinfo=pytz.utc)


def test_negative_delta_is_marked_as_a_loss(client_logged):
    account = AccountFactory()
    IncomeFactory(account=account, price=1000)
    factories.AccountWorthFactory(account=account, price=500)

    url = reverse("bookkeeping:accounts")
    content = client_logged.get(url).content.decode("utf-8")

    assert re.search(r'<td data-sign="loss">-', content)


def test_regenerate_buttons(client_logged):
    SavingFactory()

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("core:regenerate_balances")

    assert f'hx-get="{url}?type=accounts"' in content
    assert "Bus atnaujinti tik šios lentelės balansai." in content
