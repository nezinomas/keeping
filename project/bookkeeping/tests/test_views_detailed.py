import pytest
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from .. import views

pytestmark = pytest.mark.django_db


def test_view_detailed_func():
    view = resolve("/detailed/")

    assert views.Detailed == view.func.view_class


def test_view_detailed_200(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_detailed_302(client):
    url = reverse("bookkeeping:detailed")
    response = client.get(url)

    assert response.status_code == 302


def test_view_detailed_rendered_expenses(client_logged, expenses):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Expense Name" in content
    assert "Išlaidos / Expense Type" in content


def test_view_detailed_no_expenses(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Išlaidos / " not in content


def test_view_detailed_no_expenses_with_types(client_logged):
    ExpenseTypeFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Išlaidos / Expense Type" not in content


def test_view_detailed_with_incomes(client_logged):
    IncomeFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Pajamos</a></th>" in content
    assert "Income Type" in content


def test_view_detailed_no_incomes(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "<th>Pajamos</th>" not in content
    assert "Income Type</td>" not in content


def test_view_detailed_no_savings(client_logged):
    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "<th>Taupymas</th>" not in content


def test_view_detailed_with_savings(client_logged):
    SavingFactory()

    url = reverse("bookkeeping:detailed")
    response = client_logged.get(url)

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert "Taupymas</a></th>" in content
    assert "Savings</td>" in content
