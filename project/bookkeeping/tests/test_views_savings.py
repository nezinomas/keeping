from datetime import datetime

import pytest
import pytz
from django.urls import resolve, reverse

from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from .. import views
from ..factories import SavingWorthFactory

pytestmark = pytest.mark.django_db


def test_view_func():
    view = resolve("/bookkeeping/savings/")

    assert views.Savings == view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_context(client_logged):
    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.context

    assert actual["title"] == "Fondai"
    assert actual["type"] == "savings"
    assert "items" in actual
    assert "total_row" in actual
    assert "percentage_from_incomes" in actual


def test_percentage_from_incomes(client_logged):
    IncomeFactory(price=10)
    SavingFactory(price=20)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)
    actual = response.context

    assert actual["percentage_from_incomes"] == 200.0


def test_latest_check(client_logged):
    SavingFactory()
    SavingWorthFactory()
    SavingWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)

    url = reverse("bookkeeping:savings")
    response = client_logged.get(url)

    exp = [x["items"] for x in response.context if x.get("title") == "Fondai"][0][0]

    assert exp.latest_check == datetime(1999, 1, 1, 1, 3, 4, tzinfo=pytz.utc)
