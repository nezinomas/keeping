import pytest
from django.urls import resolve, reverse

from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ... import views

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                      Expenses Summary
# -------------------------------------------------------------------------------------
def test_view_func():
    view = resolve("/summary/expenses/")

    assert views.SummaryExpenses is view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_context_no_data(client_logged):
    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.get(url)
    context = response.context

    assert "form" in context


def test_view_load_form(client_logged):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.get(url)
    html = response.content.decode("utf-8")

    assert f'<option value="{t.pk}">Expense Type</option>' in html
    assert f'<option value="{t.pk}:{n.pk}">Expense Name</option>' in html


def test_view(client_logged):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()
    ExpenseFactory()

    data = {"types": [t.pk, f"{t.pk}:{n.pk}"]}

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert 'id="chart-container">' in actual
    assert '<table class="main' in actual


def test_view_no_records_for_selected_expense_name(client_logged):
    obj = ExpenseNameFactory()

    data = {"types": [obj.pk]}

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert 'id="chart-container">' not in actual
    assert '<table class="main>' not in actual


def test_view_context_found(client_logged):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()
    ExpenseFactory()

    data = {"types": [t.pk, f"{t.pk}:{n.pk}"]}

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.post(url, data)

    assert response.context["found"]
    assert "form" in response.context
    assert "categories" in response.context["chart"]
    assert "data" in response.context["chart"]
    assert "total_col" in response.context
    assert "total_row" in response.context
    assert "total" in response.context


def test_view_no_data(client_logged):
    data = {"types": []}

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert 'id="chart">' not in actual
    assert 'id="table">' not in actual
