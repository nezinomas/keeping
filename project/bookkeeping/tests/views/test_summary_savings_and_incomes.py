from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse

from ....incomes.tests.factories import IncomeFactory
from ....savings.tests.factories import SavingFactory
from ... import views

pytestmark = pytest.mark.django_db


def test_view_func():
    view = resolve("/summary/savings_and_incomes/")

    assert views.SummarySavingsAndIncomes == view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_no_logged_user(client):
    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client.get(url)

    assert response.status_code == 302


def test_view_context(client_logged):
    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert "chart_data" in actual


@time_machine.travel("2000-1-1")
def test_view_context_categories(main_user, client_logged):
    IncomeFactory(date=date(2000, 1, 1))

    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert actual["chart_data"]["categories"] == [1999, 2000]


@time_machine.travel("2000-1-1")
def test_view_context_incomes(client_logged):
    IncomeFactory(date=date(1999, 1, 1), price=1)
    IncomeFactory(date=date(2000, 1, 1), price=2)

    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert actual["chart_data"]["incomes"] == [1, 2]


@time_machine.travel("2000-1-1")
def test_view_context_incomes_one_empty_year(client_logged):
    IncomeFactory(date=date(1999, 1, 1), price=1)

    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert actual["chart_data"]["incomes"] == [1, 0]


@time_machine.travel("2000-1-1")
def test_view_context_savings(client_logged):
    SavingFactory(date=date(1999, 1, 1), price=1, fee=0)
    SavingFactory(date=date(2000, 1, 1), price=2, fee=0)

    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert actual["chart_data"]["savings"] == [1, 2]


@time_machine.travel("2000-1-1")
def test_view_contex_savings_one_empty_year(client_logged):
    SavingFactory(date=date(1999, 1, 1), price=1, fee=0)

    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert actual["chart_data"]["savings"] == [1, 0]


@time_machine.travel("2000-1-1")
def test_view_context_percents(client_logged):
    IncomeFactory(date=date(1999, 1, 1), price=10)
    SavingFactory(date=date(1999, 1, 1), price=1, fee=0)

    url = reverse("bookkeeping:summary_savings_and_incomes")
    response = client_logged.get(url)

    actual = response.context

    assert actual["chart_data"]["percents"] == [10, 0]
