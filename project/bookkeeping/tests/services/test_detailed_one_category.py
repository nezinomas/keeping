from datetime import date
from types import SimpleNamespace

import pytest

from ...services.detailed_one_category import Service, load_service


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


@pytest.fixture(name="mock_detailed_service")
def fixture_mock_detailed_service(mocker):
    module_path = "project.bookkeeping.services.detailed_one_category"

    mck_incomes = mocker.patch(f"{module_path}.IncomeModelService")
    mck_expenses = mocker.patch(f"{module_path}.ExpenseModelService")
    mck_saving = mocker.patch(f"{module_path}.SavingModelService")

    mck_context = mocker.patch.object(
        Service, "context", new_callable=mocker.PropertyMock, return_value="mck_ctx"
    )
    return SimpleNamespace(
        incomes=mck_incomes,
        expenses=mck_expenses,
        saving=mck_saving,
        context=mck_context,
    )


@pytest.mark.parametrize("category", [("pajamos"), ("incomes")])
def test_load_service_category_income(mock_detailed_service, category, main_user):
    load_service(main_user, "jan", category)

    mock_detailed_service.incomes.assert_called_once_with(main_user)
    mock_detailed_service.saving.assert_not_called()
    mock_detailed_service.expenses.assert_not_called()

    mock_detailed_service.context.assert_called_once()


@pytest.mark.parametrize("category", [("taupymas"), ("savings")])
def test_load_service_category_saving(mock_detailed_service, category, main_user):
    load_service(main_user, "jan", category)

    mock_detailed_service.incomes.assert_not_called()
    mock_detailed_service.saving.assert_called_once_with(main_user)
    mock_detailed_service.expenses.assert_not_called()
    mock_detailed_service.context.assert_called_once()


def test_load_service_category_expense(mock_detailed_service, main_user):
    load_service(main_user, "jan", "category_name")

    mock_detailed_service.incomes.assert_not_called()
    mock_detailed_service.saving.assert_not_called()
    mock_detailed_service.expenses.assert_called_once_with(main_user)

    mock_detailed_service.context.assert_called_once()
