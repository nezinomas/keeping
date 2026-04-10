from datetime import date
from types import SimpleNamespace

import pytest
import time_machine

from ...services.forecast import (
    Forecast,
    ForecastDataDTO,
    ForecastDataProvider,
    MonthlyDataFormatter,
    get_month,
)

MODULE_PATH = "project.bookkeeping.services.forecast"


def test_get_data(main_user):
    main_user.year = 1000

    data = [
        {"date": date(1000, 1, 1), "sum": 1, "title": "incomes"},
        {"date": date(1000, 12, 1), "sum": 2, "title": "incomes"},
    ]

    actual = MonthlyDataFormatter.from_monthly_sum(data)
    expect = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]

    assert actual == expect


def test_get_planned_data(main_user):
    data = [
        {"month": 1, "price": 1},
        {"month": 12, "price": 2},
    ]
    main_user.year = 1000
    actual = MonthlyDataFormatter.from_planned_data(data)
    expect = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]

    assert actual == expect


@pytest.fixture(name="data")
def fixture_data():
    return SimpleNamespace(
        incomes=[10.0, 11.0, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        expenses=[1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        savings=[4.0, 5.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        savings_close=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        planned_incomes=[0.0, 0.0, 0.0, 7.0, 8.0, 9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return SimpleNamespace(
        incomes=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        expenses=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        savings=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        savings_close=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        planned_incomes=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    )


def test_current_month(data):
    actual = Forecast(month=4, data=data).current_month()

    assert actual.expenses == 0
    assert actual.savings == 0
    assert actual.incomes == 0
    assert actual.planned_incomes == 7


def test_balance(data):
    actual = Forecast(month=4, data=data).balance()
    expect = 12.0

    assert actual == expect


def test_balance_with_savings_close(data):
    data.savings_close[2] = 2
    actual = Forecast(month=4, data=data).balance()
    expect = 14

    assert actual == expect


def test_balance_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).balance()
    expect = 0

    assert actual == expect


def test_planned_incomes(data):
    actual = Forecast(month=4, data=data).planned_incomes()
    expect = 17.0

    assert actual == expect


def test_planned_incomes_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).planned_incomes()
    expect = 0

    assert actual == expect


def test_planned_incomes_only_planned_data(data_empty):
    data_empty.planned_incomes[3] = 1
    actual = Forecast(month=1, data=data_empty).planned_incomes()
    expect = 1

    assert actual == expect


def test_averages_data_with_six_months(data):
    data.expenses[3] = 6.0
    data.expenses[4] = 16.0
    data.expenses[5] = 26.0
    data.savings[3] = 7.0
    data.savings[4] = 17.0
    data.savings[5] = 27.0

    actual = Forecast(month=7, data=data).medians()

    assert actual.expenses == 4.5
    assert actual.savings == 6.5


def test_averages_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).medians()
    expect = {"expenses": 0, "savings": 0}

    assert actual.expenses == 0
    assert actual.savings == 0


def test_forecast(data):
    actual = Forecast(month=4, data=data).forecast()
    expect = -27

    assert actual == expect


def test_forecast_with_savings_close(data):
    data.savings_close[2] = 2
    actual = Forecast(month=4, data=data).forecast()
    expect = -25

    assert actual == expect


def test_forecast_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).forecast()
    expect = 0

    assert actual == expect


def test_forecast_only_planned_data(data_empty):
    data_empty.planned_incomes[3] = 1
    actual = Forecast(month=1, data=data_empty).forecast()
    expect = 1

    assert actual == expect


def test_forecast_current_month_expenses_exceeds_average(data):
    data.expenses[3] = 100

    actual = Forecast(month=4, data=data).forecast()
    expect = -125

    assert actual == expect


def test_forecast_current_month_incomes_exceeds_planned(data):
    data.incomes[3] = 100

    actual = Forecast(month=4, data=data).forecast()
    expect = 66

    assert actual == expect


def test_forecast_current_month_savings_exceeds_average(data):
    data.savings[3] = 100

    actual = Forecast(month=4, data=data).forecast()
    expect = -122

    assert actual == expect


@time_machine.travel("1999-3-1")
@pytest.mark.parametrize(
    "year, expected",
    [
        (1999, 3),
        (1998, 12),
        (2000, 1),
    ],
)
def test_get_month(year, expected):
    assert get_month(year) == expected


def test_forecast_data_dto():
    dto = ForecastDataDTO(
        incomes=[10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        expenses=[5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        savings=[2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        savings_close=[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        planned_incomes=[20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    )

    assert dto.incomes == [10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert dto.planned_incomes == [20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def test_monthly_data_formatter_from_planned_data():
    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]
    data = [
        {"month": 1, "price": 5},
        {"month": 12, "price": 8},
    ]

    actual = MonthlyDataFormatter.from_planned_data(data, months)
    expect = [5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0]

    assert actual == expect


def test_forecast_data_provider_get_forecast_data(mocker, main_user):
    main_user.year = 1000

    # 1. Mock the services to return fake database QuerySets
    mock_income = mocker.patch(f"{MODULE_PATH}.IncomeModelService")
    mock_income.return_value.sum_by_month.return_value = [
        {"date": date(1000, 1, 1), "sum": 100}
    ]

    mock_expense = mocker.patch(f"{MODULE_PATH}.ExpenseModelService")
    mock_expense.return_value.sum_by_month.return_value = [
        {"date": date(1000, 2, 1), "sum": 50}
    ]

    mock_saving = mocker.patch(f"{MODULE_PATH}.SavingModelService")
    mock_saving.return_value.sum_by_month.return_value = []

    mock_saving_close = mocker.patch(f"{MODULE_PATH}.SavingCloseModelService")
    mock_saving_close.return_value.sum_by_month.return_value = []

    mock_plan = mocker.patch(f"{MODULE_PATH}.IncomePlanModelService")
    mock_plan.return_value.year.return_value.values.return_value = [
        {"month": 1, "price": 200}
    ]

    # 2. Execute the provider
    provider = ForecastDataProvider(main_user)
    result = provider.get_forecast_data()

    # 3. Assert the DTO is structured correctly based on the mocked data
    assert isinstance(result, ForecastDataDTO)
    assert result.incomes[0] == 100.0  # January Income
    assert result.expenses[1] == 50.0  # February Expense
    assert result.savings[0] == 0.0  # Empty fallback
    assert result.planned_incomes[0] == 200.0  # January Planned Income


def test_forecast_data_provider_get_beginning_balance(mocker, main_user):
    main_user.year = 1000

    # Mock the chained database calls: objects.filter().aggregate()
    mock_balance_service = mocker.patch(f"{MODULE_PATH}.AccountBalanceModelService")
    mock_filter = mock_balance_service.return_value.objects.filter.return_value
    mock_filter.aggregate.return_value = {"past__sum": 1500}

    provider = ForecastDataProvider(main_user)
    actual = provider.get_beginning_balance()

    assert actual == 1500
    mock_balance_service.return_value.objects.filter.assert_called_once_with(year=1000)
    mock_filter.aggregate.assert_called_once()
