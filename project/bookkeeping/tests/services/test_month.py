from datetime import date

import pytest

from project.bookkeeping.lib.make_dataframe import MakeDataFrame

from ...services.month.builders import ChartBuilder, InfoBuilder, MonthTableBuilder
from ...services.month.dtos import InfoState, MonthDataDTO
from ...services.month.presenters import MonthContextPresenter

MONTH_SERVICE_PATH = "project.bookkeeping.services.month"


# -------------------------------------------------------------------------------------
#                                                                              Fixtures
# -------------------------------------------------------------------------------------
@pytest.fixture
def dummy_dto():
    """A static payload representing the data fetched from the DB."""
    return MonthDataDTO(
        incomes=1000,
        expenses=[{"date": "2026-04-01", "Food": 10}],
        expense_types=["Food"],
        necessary_expense_types=["Food"],
        savings=[{"date": "2026-04-01", "savings": 50}],
        plans_data={"dummy_plan_key": "dummy_plan_value"},
        targets={"Food": 100},
    )



def test_chart_expenses_context():
    totals = {"xyz": 10, "Taupymas": 1}
    targets = {"xyz": 6, "Taupymas": 9}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_expenses()

    assert len(actual) == 2
    assert actual[0]["name"] == "XYZ"
    assert actual[1]["name"] == "TAUPYMAS"


def test_chart_expenses():
    totals = {"T1": 25, "T2": 50}
    obj = ChartBuilder(totals=totals, targets={})

    actual = obj.build_expenses()

    expect = [
        {"name": "T2", "y": 50},
        {"name": "T1", "y": 25},
    ]

    assert actual == expect


def test_chart_expenses_colors_shorter_then_data():
    totals = {"T1": 2, "T2": 5, "T3": 1}
    obj = ChartBuilder(targets={}, totals=totals)

    actual = obj.build_expenses()

    expect = [
        {"name": "T2", "y": 5},
        {"name": "T1", "y": 2},
        {"name": "T3", "y": 1},
    ]

    assert actual == expect


def test_chart_expenses_no_expenes_data():
    obj = ChartBuilder(targets={}, totals={})

    actual = obj.build_expenses()

    assert actual == []


def test_build_targets_context():
    obj = ChartBuilder(targets={}, totals={})
    actual = obj.build_targets()

    assert "categories" in actual
    assert "target" in actual
    assert "targetTitle" in actual
    assert "fact" in actual
    assert "factTitle" in actual


def test_build_targets_context_with_savings():
    totals = {"xxx": 6, "Taupymas": 99}
    targets = {"xxx": 6, "Taupymas": 9}
    obj = ChartBuilder(targets, totals)
    actual = obj.build_targets()

    assert actual["categories"] == ["TAUPYMAS", "XXX"]
    assert actual["target"] == [9, 6]
    assert actual["fact"] == [{"y": 99, "target": 9}, {"y": 6, "target": 6}]


def test_build_targets_categories():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    expect = ["T2", "T1"]

    assert actual["categories"] == expect


def test_build_targets_data_target():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    assert actual["target"] == [4, 3]


def test_build_targets_data_target_empty():
    totals = {"T1": 2, "T2": 5}
    targets = {}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    assert actual["target"] == [0, 0]


def test_build_targets_data_fact():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    expect = [
        {"y": 5, "target": 4},
        {"y": 2, "target": 3},
    ]

    assert actual["fact"] == expect


def test_build_targets_data_fact_no_target():
    totals = {"T1": 2, "T2": 5}
    targets = {}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    expect = [
        {"y": 5, "target": 0},
        {"y": 2, "target": 0},
    ]

    assert actual["fact"] == expect


@pytest.fixture(name="df_expense")
def fixture_df_expense():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 2), "title": "A", "sum": 4, "exception_sum": 0}]
    columns = ["A", "B"]

    return MakeDataFrame(year=year, month=month, data=data, columns=columns).data


@pytest.fixture(name="df_saving")
def fixture_df_saving():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 3), "sum": 2, "title": "savings"}]

    return MakeDataFrame(year=year, month=month, data=data).data


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
    print(f'--------------------------->\n{obj.df}\n')
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


# -------------------------------------------------------------------------------------
#                                                           MonthContextPresenter Tests
# -------------------------------------------------------------------------------------


def test_presenter_init(dummy_dto):
    """Proves the constructor only assigns state and does not trigger heavy logic."""
    presenter = MonthContextPresenter(2026, 4, dummy_dto)

    assert presenter.year == 2026
    assert presenter.month == 4
    assert presenter.dto == dummy_dto


def test_month_table_property(mocker, dummy_dto):
    """Proves MakeDataFrame and MonthTableBuilder are initialized correctly."""
    # Mock the external dependencies
    mock_make_df = mocker.patch(f"{MONTH_SERVICE_PATH}.presenters.MakeDataFrame")
    mock_table_builder = mocker.patch(f"{MONTH_SERVICE_PATH}.presenters.MonthTableBuilder")

    presenter = MonthContextPresenter(2026, 4, dummy_dto)
    _ = presenter.month_table  # Trigger the cached property

    # Ensure DataFrames were generated for both expenses and savings
    assert mock_make_df.call_count == 2
    mock_table_builder.assert_called_once()


def test_plans_property(mocker, dummy_dto):
    """Proves PlanCalculateDaySum is initialized directly with DTO data."""
    # We no longer need to mock PlanCollectData!
    mock_calc = mocker.patch(f"{MONTH_SERVICE_PATH}.presenters.PlanCalculateDaySum")

    presenter = MonthContextPresenter(2026, 4, dummy_dto)
    result = presenter.plans 

    # Verify the calculator receives the exact data stored in the DTO
    mock_calc.assert_called_once_with(
        data={"dummy_plan_key": "dummy_plan_value"}, 
        month=4
    )
    assert result == mock_calc.return_value


def test_spending_property(mocker, dummy_dto):
    """Proves DaySpending is initialized with the correct plan parameters."""
    mock_make_df = mocker.patch(f"{MONTH_SERVICE_PATH}.presenters.MakeDataFrame")
    mock_day_spending = mocker.patch(f"{MONTH_SERVICE_PATH}.presenters.DaySpending")

    # Mock the 'plans' cached property so we don't trigger its real logic
    mock_plans = mocker.Mock(day_input=15, expenses_free=200)
    mocker.patch.object(
        MonthContextPresenter,
        "plans",
        new_callable=mocker.PropertyMock,
        return_value=mock_plans,
    )

    presenter = MonthContextPresenter(2026, 4, dummy_dto)
    result = presenter.spending

    mock_day_spending.assert_called_once_with(
        expense=mock_make_df.return_value,
        necessary=["Food"],
        per_day=15,
        free=200,
    )
    assert result == mock_day_spending.return_value


def test_totals_property(mocker, dummy_dto):
    """Proves dictionary keys are accessed safely and mapped correctly."""
    presenter = MonthContextPresenter(2026, 4, dummy_dto)

    # Mock the 'month_table' and 'spending' properties
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
        "income": 1000,  # From DTO
        "expense": 400,  # From table total_row
        "saving": 50,  # From table total_row
        "avg_per_day": 12,  # From spending
    }


def test_tables_property(mocker, dummy_dto):
    """Proves the tables dictionary is built from the nested properties."""
    presenter = MonthContextPresenter(2026, 4, dummy_dto)

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


def test_charts_property(mocker, dummy_dto):
    """Proves the ChartBuilder receives targets directly from the DTO."""
    mock_chart_builder = mocker.patch(f"{MONTH_SERVICE_PATH}.presenters.ChartBuilder")

    # Presenter initialized without a user!
    presenter = MonthContextPresenter(2026, 4, dummy_dto)

    mock_month_table = mocker.Mock(total_row={"total": 10})
    mocker.patch.object(
        MonthContextPresenter, "month_table", new_callable=mocker.PropertyMock, return_value=mock_month_table
    )

    result = presenter.charts

    # We no longer need to mock PlanAggregatorService because it is handled by the DTO
    mock_chart_builder.assert_called_once_with(
        targets={"Food": 100}, # Pulls directly from dummy_dto.targets
        totals={"total": 10}
    )
    assert result == mock_chart_builder.return_value
