from datetime import datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ...savings.factories import SavingFactory
from .. import factories, views

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


def test_regenerate_buttons(client_logged):
    SavingFactory()

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    url = reverse("core:regenerate_balances")

    assert f'hx-get="{url}?type=accounts"' in content
    assert "Bus atnaujinti tik šios lentelės balansai." in content
