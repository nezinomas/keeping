from datetime import date

import pytest
from django.urls import resolve, reverse

from ....expenses.tests.factories import ExpenseFactory
from ... import views

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                                 Month
# -------------------------------------------------------------------------------------
def test_view_month_func():
    view = resolve("/month/")

    assert views.Month == view.func.view_class


def test_view_month_200(client_logged):
    url = reverse("bookkeeping:month")
    response = client_logged.get(url)

    assert response.status_code == 200


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


# -------------------------------------------------------------------------------------
#                                                                        Month Day List
# -------------------------------------------------------------------------------------
def test_view_expand_day_expenses_func():
    view = resolve("/month/1111-2-3/")

    assert views.ExpandDayExpenses == view.func.view_class


def test_view_expand_day_expenses_200(client_logged):
    url = reverse("bookkeeping:expand_day_expenses", kwargs={"date": date(1999, 1, 1)})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_expand_day_expenses_str_in_url(client_logged):
    url = reverse("bookkeeping:expand_day_expenses", kwargs={"date": "xx"})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")
    assert response.status_code == 200

    assert "1974-01-01" in actual


@pytest.mark.parametrize(
    "dt, expect",
    [
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


# -------------------------------------------------------------------------------------
#                                                                          Month Charts
# -------------------------------------------------------------------------------------
def test_view_month_chart_func():
    view = resolve("/month/chart_type")

    assert views.MonthChart == view.func.view_class


def test_view_month_chart_200(client_logged):
    url = reverse("bookkeeping:month_chart", kwargs={"chart_type": "xxx"})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_month_chart_302(client):
    url = reverse("bookkeeping:month_chart", kwargs={"chart_type": "xxx"})
    response = client.get(url)

    assert response.status_code == 302
