import re
from datetime import date

import pytest
from django.urls import reverse

from ....expenses.tests.factories import ExpenseFactory
from ....plans.tests.factories import DayPlanFactory

pytestmark = pytest.mark.django_db


def test_view_month_import_button_after_expenses_button(client_logged):
    url = reverse("bookkeeping:month")
    response = client_logged.get(url)
    text = response.content.decode()

    expenses_url = reverse("expenses:new")
    import_url = reverse("expenses:import")

    assert 'class="button-outline-success import-receipt"' in text
    assert f'href="{import_url}"' in text
    assert "Importuoti čekį" in text
    assert text.index(expenses_url) < text.index(import_url)


def test_view_month_day_over_budget_is_marked_as_a_loss(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    url = reverse("bookkeeping:month")
    text = client_logged.get(url, {"month": 1}).content.decode()

    assert re.search(r'<td data-sign="loss" class="day-warning[ "]', text)
    assert "table-danger" not in text


def test_view_month_day_cells_within_budget_carry_no_sign(client_logged):
    DayPlanFactory(year=1999, month=1, price=1000000)
    ExpenseFactory(date=date(1999, 1, 1), price=1)

    url = reverse("bookkeeping:month")
    text = client_logged.get(url, {"month": 1}).content.decode()
    cells = re.findall(r'<td([^>]*)class="day-(?:warning|negative)[ "]', text)

    assert cells
    assert all("data-sign" not in attrs for attrs in cells)


def test_view_month_negative_cumulative_balance_is_marked_as_a_loss(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    url = reverse("bookkeeping:month")
    text = client_logged.get(url, {"month": 1}).content.decode()

    assert re.search(r'<td data-sign="loss" class="day-negative[ "]', text)


def test_view_month_plan_table_rows_carry_their_sign(client_logged):
    ExpenseFactory(date=date(1999, 1, 1), price=100)

    url = reverse("bookkeeping:month")
    text = client_logged.get(url, {"month": 1}).content.decode()
    signs = re.findall(r'<tr data-sign="(\w*)">', text)

    assert signs[:3] == ["gain", "loss", "gain"]


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 1),
        ("x", 12),
    ],
)
def test_view_month_200_set_user_month_value(month, expect, client_logged):
    url = reverse("bookkeeping:month")
    response = client_logged.get(url, {"month": month})

    assert response.wsgi_request.user.month == expect


@pytest.mark.parametrize(
    "dt, expect",
    [
        ("xx", "1974-01-01 dieną įrašų nėra"),
        ("1970-13-01", "1974-01-01 dieną įrašų nėra"),
        ("1970-12-32", "1974-01-01 dieną įrašų nėra"),
    ],
)
def test_view_expand_day_expenses_wrong_dates(dt, expect, client_logged):
    url = reverse("bookkeeping:expand_day_expenses", kwargs={"date": dt})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert expect in actual


def test_view_expand_day_expenses_ajax(client_logged):
    ExpenseFactory()

    url = reverse("bookkeeping:expand_day_expenses", kwargs={"date": date(1999, 1, 1)})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Expense Type" in actual
    assert "Expense Name" in actual


@pytest.mark.parametrize(
    "chart_type, script",
    [
        pytest.param("targets", "chart_month_targets.js", id="targets"),
        pytest.param("expenses", "chart_month_expenses.js", id="expenses"),
        pytest.param("xxx", "chart_month_expenses.js", id="unknown_is_expenses"),
    ],
)
def test_view_month_chart_loads_its_script(client_logged, chart_type, script):
    url = reverse("bookkeeping:month_chart", kwargs={"chart_type": chart_type})
    content = client_logged.get(url).content.decode("utf-8")

    assert f'src="/static/js/{script}"' in content


def test_view_month_chart_302(client):
    url = reverse("bookkeeping:month_chart", kwargs={"chart_type": "xxx"})
    response = client.get(url)

    assert response.status_code == 302
