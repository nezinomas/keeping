import pytest
from django.urls import reverse

from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ..helper import script_json

pytestmark = pytest.mark.django_db


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

    chart = script_json(actual, "chart-data")
    assert 'id="chart-container">' in actual
    assert chart["categories"] == [1999]
    assert [row["data"] for row in chart["data"]] == [[112.0], [112.0]]
    assert '<table class="main' in actual
    assert '<td class="text-left">Expense Type</td>' in actual
    assert actual.count('<th data-cell="">2,24</th>') == 2


def test_view_no_records_for_selected_expense_name(client_logged):
    obj = ExpenseNameFactory()

    data = {"types": [obj.pk]}

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert 'id="chart-container">' not in actual
    assert '<table class="main' not in actual


def test_view_no_data(client_logged):
    data = {"types": []}

    url = reverse("bookkeeping:summary_expenses")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert 'id="chart-container">' not in actual
    assert '<table class="main' not in actual
