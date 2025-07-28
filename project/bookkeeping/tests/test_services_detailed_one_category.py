from datetime import date

import pytest
from mock import PropertyMock, patch

from ..services.detailed_one_category import Service, load_service


@pytest.fixture(name="data")
def fixure_data():
    return [
        {"date": date(2021, 1, 1), "sum": 12, "title": "X", "type_title": "T2"},
        {"date": date(2021, 11, 1), "sum": 1, "title": "X", "type_title": "T2"},
        {"date": date(2021, 1, 1), "sum": 2, "title": "Y", "type_title": "T2"},
        {"date": date(2021, 11, 1), "sum": 24, "title": "Y", "type_title": "T2"},
    ]


def test_order_by_title_no_data():
    actual = Service(2021, [], order="title").context

    assert actual == {}


def test_order_by_title(data):
    actual = Service(2021, data, order="title").context

    assert actual["name"] == "Išlaidos / T2"

    assert actual["items"][0]["title"] == "X"
    assert actual["items"][0]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]
    assert actual["items"][1]["title"] == "Y"
    assert actual["items"][1]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [13.0, 26.0]
    assert actual["total"] == 39.0


def test_order_by_title_for_savings():
    data = [
        {"date": date(2021, 1, 1), "sum": 12, "title": "X"},
        {"date": date(2021, 11, 1), "sum": 1, "title": "X"},
        {"date": date(2021, 1, 1), "sum": 2, "title": "Y"},
        {"date": date(2021, 11, 1), "sum": 24, "title": "Y"},
    ]
    actual = Service(2021, data, order="title", category="savings").context

    assert actual["name"] == "Taupymas"

    assert actual["items"][0]["title"] == "X"
    assert actual["items"][0]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]
    assert actual["items"][1]["title"] == "Y"
    assert actual["items"][1]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [13.0, 26.0]
    assert actual["total"] == 39.0


def test_order_by_month_november(data):
    actual = Service(2021, data, order="nov").context

    assert actual["name"] == "Išlaidos / T2"

    assert actual["items"][0]["title"] == "Y"
    assert actual["items"][0]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]
    assert actual["items"][1]["title"] == "X"
    assert actual["items"][1]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [26.0, 13.0]
    assert actual["total"] == 39.0


def test_order_by_total_col(data):
    actual = Service(2021, data, order="total").context

    assert actual["name"] == "Išlaidos / T2"

    assert actual["items"][0]["title"] == "Y"
    assert actual["items"][0]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]
    assert actual["items"][1]["title"] == "X"
    assert actual["items"][1]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [26.0, 13.0]
    assert actual["total"] == 39.0


@patch("project.incomes.models.Income.objects.sum_by_month_and_type")
@patch("project.expenses.models.Expense.objects.sum_by_month_and_name")
@patch("project.savings.models.Saving.objects.sum_by_month_and_type")
@patch.object(Service, "context", new_callable=PropertyMock, return_value="mocked_context")
def test_load_service_category_income(
    mck_service, mck_saving, mck_expenses, mck_incomes
):
    year = 2021
    order = "jan"
    category = "pajamos"

    load_service(year, order, category)

    assert mck_incomes.called
    assert not mck_saving.called
    assert not mck_expenses.called

    assert mck_service.called


@patch("project.incomes.models.Income.objects.sum_by_month_and_type")
@patch("project.expenses.models.Expense.objects.sum_by_month_and_name")
@patch("project.savings.models.Saving.objects.sum_by_month_and_type")
@patch.object(Service, "context", new_callable=PropertyMock, return_value="mocked_context")
def test_load_service_category_saving(
    mck_service, mck_saving, mck_expenses, mck_incomes
):
    year = 2021
    order = "jan"
    category = "taupymas"

    ctx = load_service(year, order, category)
    assert ctx == "mocked_context"

    assert not mck_incomes.called
    assert mck_saving.called
    assert not mck_expenses.called


@patch("project.incomes.models.Income.objects.sum_by_month_and_type")
@patch("project.expenses.models.Expense.objects.sum_by_month_and_name")
@patch("project.savings.models.Saving.objects.sum_by_month_and_type")
@patch.object(Service, "context", new_callable=PropertyMock, return_value="mocked_context")
def test_load_service_category_expense(
    mck_service, mck_saving, mck_expenses, mck_incomes
):
    year = 2021
    order = "jan"
    category = "category_name"

    ctx = load_service(year, order, category)
    assert ctx == "mocked_context"

    assert not mck_incomes.called
    assert not mck_saving.called
    assert mck_expenses.called
