from datetime import date

import pytest

from project.bookkeeping.lib.make_dataframe import MakeDataFrame

from ....plans.lib.calc_day_sum import DataDto
from ...services.month.builders import ChartBuilder, InfoBuilder, MonthTableBuilder
from ...services.month.dtos import InfoState, MonthDataDTO
from ...services.month.presenters import MonthContextPresenter

PLAN_MONTHS = range(1, 13)


@pytest.fixture(name="month_dto")
def fixture_month_dto():
    plans = DataDto(
        incomes=[{"month": m, "amount": 3000} for m in PLAN_MONTHS],
        expenses_regular=[],
        expenses_necessary=[{"month": m, "amount": 200} for m in PLAN_MONTHS],
        savings=[],
        per_day=[{"month": m, "amount": 10 * m} for m in PLAN_MONTHS],
        necessary=[{"month": m, "amount": 100} for m in PLAN_MONTHS],
        month_len=[{"month": m, "amount": 30} for m in PLAN_MONTHS],
    )
    return MonthDataDTO(
        incomes=1000,
        expenses=[
            {"date": date(2026, 4, 1), "title": "Food", "sum": 10, "exception_sum": 0},
            {"date": date(2026, 4, 1), "title": "Rent", "sum": 500, "exception_sum": 0},
        ],
        expense_types=["Food", "Rent"],
        necessary_expense_types=["Rent"],
        savings=[{"date": date(2026, 4, 1), "sum": 50, "title": "savings"}],
        plans_data=plans,
        targets={"Food": 100},
    )


@pytest.mark.parametrize(
    "targets, totals, expect",
    [
        pytest.param(
            {"xyz": 6, "Taupymas": 9},
            {"xyz": 10, "Taupymas": 1},
            [{"name": "XYZ", "y": 10}, {"name": "TAUPYMAS", "y": 1}],
            id="upper_case_names",
        ),
        pytest.param(
            {},
            {"T1": 25, "T2": 50},
            [{"name": "T2", "y": 50}, {"name": "T1", "y": 25}],
            id="sorted_two",
        ),
        pytest.param(
            {},
            {"T1": 2, "T2": 5, "T3": 1},
            [
                {"name": "T2", "y": 5},
                {"name": "T1", "y": 2},
                {"name": "T3", "y": 1},
            ],
            id="sorted_three",
        ),
        pytest.param({}, {}, [], id="no_data"),
    ],
)
def test_chart_expenses(targets, totals, expect):
    actual = ChartBuilder(targets=targets, totals=totals).build_expenses()

    assert actual == expect


def test_build_targets_without_data():
    actual = ChartBuilder(targets={}, totals={}).build_targets()

    assert actual == {
        "categories": [],
        "target": [],
        "targetTitle": "Planas",
        "fact": [],
        "factTitle": "Faktas",
        "max_category_len": 0,
    }


@pytest.mark.parametrize(
    "targets, totals, categories, target, fact, max_category_len",
    [
        pytest.param(
            {"xxx": 6, "Taupymas": 9},
            {"xxx": 6, "Taupymas": 99},
            ["TAUPYMAS", "XXX"],
            [9, 6],
            [{"y": 99, "target": 9}, {"y": 6, "target": 6}],
            8,
            id="upper_case_names",
        ),
        pytest.param(
            {"T1": 3, "T2": 4},
            {"T1": 2, "T2": 5},
            ["T2", "T1"],
            [4, 3],
            [{"y": 5, "target": 4}, {"y": 2, "target": 3}],
            2,
            id="sorted_by_total",
        ),
        pytest.param(
            {},
            {"T1": 2, "T2": 5},
            ["T2", "T1"],
            [0, 0],
            [{"y": 5, "target": 0}, {"y": 2, "target": 0}],
            2,
            id="no_targets",
        ),
        pytest.param(
            {},
            {"savings": 5, "ab": 1},
            ["TAUPYMAS", "AB"],
            [0, 0],
            [{"y": 5, "target": 0}, {"y": 1, "target": 0}],
            8,
            id="translated_savings_name",
        ),
    ],
)
def test_build_targets(targets, totals, categories, target, fact, max_category_len):
    actual = ChartBuilder(targets, totals).build_targets()

    assert actual["categories"] == categories
    assert actual["target"] == target
    assert actual["fact"] == fact
    assert actual["max_category_len"] == max_category_len


@pytest.fixture(name="df_expense")
def fixture_df_expense():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 2), "title": "A", "sum": 4, "exception_sum": 0}]
    columns = ["A", "B"]

    return MakeDataFrame.for_month(
        year=year, month=month, data=data, columns=columns
    ).data


@pytest.fixture(name="df_saving")
def fixture_df_saving():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 3), "sum": 2, "title": "savings"}]

    return MakeDataFrame.for_month(year=year, month=month, data=data).data


def test_main_table(df_expense, df_saving):
    actual = MonthTableBuilder(df_expense, df_saving).table

    assert len(actual) == 31
    assert actual[0] == {
        "date": date(1999, 3, 1),
        "A": 0,
        "B": 0,
        "total": 0,
        "savings": 0,
    }
    assert actual[1] == {
        "date": date(1999, 3, 2),
        "A": 4,
        "B": 0,
        "total": 4,
        "savings": 0,
    }
    assert actual[2] == {
        "date": date(1999, 3, 3),
        "A": 0,
        "B": 0,
        "total": 0,
        "savings": 2,
    }


def test_main_table_total_row(df_expense, df_saving):
    obj = MonthTableBuilder(df_expense, df_saving)
    actual = obj.total_row

    assert actual == {"A": 4, "B": 0, "total": 4, "savings": 2}


def test_info_builder_delta():
    fact = InfoState(income=9, saving=8, expense=7, per_day=6, balance=5)
    plan = InfoState(income=1, saving=2, expense=3, per_day=4, balance=4)

    actual = InfoBuilder.build(fact, plan)

    assert actual["fact"] == {
        "income": 9,
        "saving": 8,
        "expense": 7,
        "per_day": 6,
        "balance": 5,
    }
    assert actual["plan"] == {
        "income": 1,
        "saving": 2,
        "expense": 3,
        "per_day": 4,
        "balance": 4,
    }
    assert actual["delta"] == {
        "income": 8,
        "saving": -6,
        "expense": -4,
        "per_day": -2,
        "balance": 1,
    }


def test_plans_property(month_dto):
    plans = MonthContextPresenter(2026, 4, month_dto).plans

    assert plans.day_input == 40
    assert plans.expenses_free == 2700


def test_spending_property(month_dto):
    spending = MonthContextPresenter(2026, 4, month_dto).spending

    assert spending.spending[0] == {
        "date": date(2026, 4, 1),
        "total": 10,
        "day": 30,
        "teoretical": 2660,
        "real": 2690,
        "full": 30,
    }


def test_totals_property(mocker, month_dto):
    presenter = MonthContextPresenter(2026, 4, month_dto)

    mock_month_table = mocker.Mock()
    mock_month_table.total_row = {"total": 400, "savings": 50}

    mock_spending = mocker.Mock(avg_per_day=12)

    mocker.patch.object(
        MonthContextPresenter,
        "month_table",
        new_callable=mocker.PropertyMock,
        return_value=mock_month_table,
    )
    mocker.patch.object(
        MonthContextPresenter,
        "spending",
        new_callable=mocker.PropertyMock,
        return_value=mock_spending,
    )

    actual = presenter.totals

    assert actual == {
        "income": 1000,
        "expense": 400,
        "saving": 50,
        "avg_per_day": 12,
    }


def test_tables_property(mocker, month_dto):
    presenter = MonthContextPresenter(2026, 4, month_dto)

    mock_month_table = mocker.Mock(table=["main_data"], total_row={"total": 10})
    mock_spending = mocker.Mock(spending=["spending_data"])

    mocker.patch.object(
        MonthContextPresenter,
        "month_table",
        new_callable=mocker.PropertyMock,
        return_value=mock_month_table,
    )
    mocker.patch.object(
        MonthContextPresenter,
        "spending",
        new_callable=mocker.PropertyMock,
        return_value=mock_spending,
    )

    assert presenter.tables == {
        "main_table": ["main_data"],
        "spending_table": ["spending_data"],
        "total_row": {"total": 10},
    }


def test_charts_property(month_dto):
    charts = MonthContextPresenter(2026, 4, month_dto).charts

    assert charts.build_targets()["fact"] == [
        {"y": 500, "target": 0},
        {"y": 50, "target": 0},
        {"y": 10, "target": 100},
    ]
