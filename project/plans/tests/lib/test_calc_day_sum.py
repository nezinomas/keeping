import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.calc_day_sum import CalcRow, InputRow, PlanCalculateDaySum, PlanCollectData

MONTH_LEN = [
    {"month": 1, "amount": 31},
    {"month": 2, "amount": 29},
    {"month": 3, "amount": 31},
    {"month": 4, "amount": 30},
    {"month": 5, "amount": 31},
    {"month": 6, "amount": 30},
    {"month": 7, "amount": 31},
    {"month": 8, "amount": 31},
    {"month": 9, "amount": 30},
    {"month": 10, "amount": 31},
    {"month": 11, "amount": 30},
    {"month": 12, "amount": 31},
]


def make_data():
    obj = type("PlanCollectData", (object,), {})
    obj.incomes = [
        {"month": 1, "amount": 900},
        {"month": 2, "amount": 1000},
        {"month": 3, "amount": 450},
        {"month": 4, "amount": 450},
        {"month": 5, "amount": 450},
        {"month": 6, "amount": 450},
        {"month": 7, "amount": 450},
        {"month": 8, "amount": 450},
        {"month": 9, "amount": 450},
        {"month": 10, "amount": 450},
        {"month": 11, "amount": 450},
        {"month": 12, "amount": 450},
    ]

    obj.expenses_regular = [
        {"month": 1, "amount": 260},
        {"month": 2, "amount": 280},
    ]

    obj.expenses_necessary = [
        {"month": 1, "amount": 300},
        {"month": 2, "amount": 320},
    ]

    obj.savings = [
        {"month": 1, "amount": 190},
        {"month": 2, "amount": 200},
    ]

    obj.per_day = [
        {"month": 1, "amount": 25},
        {"month": 2, "amount": 26},
    ]

    obj.necessary = [
        {"month": 2, "amount": 100},
    ]

    obj.month_len = MONTH_LEN

    return obj


@pytest.fixture(name="data")
def fixture_data():
    return make_data()


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return type(
        "PlanCollectData",
        (object,),
        {
            "incomes": [],
            "expenses_regular": [],
            "expenses_necessary": [],
            "savings": [],
            "per_day": [],
            "necessary": [],
            "month_len": MONTH_LEN,
        },
    )


def test_get_row_of_an_unknown_name_is_an_empty_dict(data):
    actual = PlanCalculateDaySum(data).get_row("xxx")

    assert actual == {}


def test_incomes_no_data(data_empty):
    actual = PlanCalculateDaySum(data_empty).get_row("incomes")

    assert actual["1"] == 0
    assert actual["12"] == 0


# Pinned values of the one fixture dataset; day_calced is held to the cent.
CENT = 0.005
TWELVE_MONTHS = [
    pytest.param("incomes", {1: 900, 2: 1000, 12: 450}, id="incomes"),
    pytest.param("incomes_avg", {1: 450, 2: 450}, id="incomes_avg"),
    pytest.param("savings", {1: 190, 2: 200}, id="savings"),
    pytest.param("expenses_regular", {1: 260, 2: 280}, id="expenses_regular"),
    pytest.param("expenses_necessary", {1: 490, 2: 620, 3: 0}, id="expenses_necessary"),
    pytest.param("expenses_free", {1: -40, 2: -170, 3: 450}, id="expenses_free"),
    pytest.param("expenses_full", {1: 750, 2: 900, 3: 0}, id="expenses_full_row"),
    pytest.param(
        "expenses_remains", {1: -300, 2: -450, 3: 450}, id="expenses_remains_row"
    ),
    pytest.param("day_input", {1: 25, 2: 26}, id="day_input"),
    pytest.param(
        "day_calced",
        {
            1: pytest.approx(-1.29, abs=CENT),
            2: pytest.approx(-5.86, abs=CENT),
            3: pytest.approx(14.52, abs=CENT),
            4: pytest.approx(15.00, abs=CENT),
            5: pytest.approx(14.52, abs=CENT),
            6: pytest.approx(15.00, abs=CENT),
        },
        id="day_calced",
    ),
    pytest.param("remains", {1: -815, 2: -924, 3: 450}, id="remains"),
    pytest.param("necessary", {1: 0, 2: 100, 3: 0}, id="additional_necessary"),
    pytest.param("month_len", {1: 31}, id="properties_month_len"),
]


@pytest.mark.parametrize("row, cells", TWELVE_MONTHS)
def test_row_of_twelve_months(row, cells, data):
    actual = PlanCalculateDaySum(data).get_row(row)

    assert len(actual) == 12
    for month, expect in cells.items():
        assert actual[str(month)] == expect


@example(row="incomes", month=1)
@example(row="savings", month=1)
@example(row="expenses_free", month=1)
@example(row="expenses_free", month=2)
@example(row="expenses_free", month=3)
@example(row="expenses_remains", month=1)
@example(row="expenses_remains", month=2)
@example(row="expenses_remains", month=3)
@example(row="expenses_necessary", month=1)
@example(row="expenses_necessary", month=2)
@example(row="expenses_necessary", month=3)
@example(row="expenses_full", month=1)
@example(row="expenses_full", month=2)
@example(row="expenses_full", month=3)
@example(row="day_calced", month=1)
@example(row="day_calced", month=2)
@example(row="day_calced", month=3)
@example(row="day_calced", month=4)
@example(row="day_calced", month=5)
@example(row="day_calced", month=6)
@example(row="remains", month=1)
@example(row="remains", month=2)
@example(row="remains", month=3)
@example(row="necessary", month=1)
@example(row="necessary", month=2)
@example(row="necessary", month=3)
@example(row="incomes_avg", month=1)
@example(row="expenses_regular", month=1)
@example(row="day_input", month=1)
@example(row="month_len", month=1)
@given(row=st.sampled_from([*InputRow, *CalcRow]), month=st.integers(1, 12))
def test_row_of_one_month_is_its_cell_of_twelve(row, month):
    data = make_data()

    actual = PlanCalculateDaySum(data, month).get_row(row)

    assert actual == PlanCalculateDaySum(data).get_row(row)[str(month)]


def test_remains_only_necessary_expenses(data):
    data.necessary = [
        {"month": 5, "amount": 12500},
    ]
    actual = PlanCalculateDaySum(data).get_row("remains")

    assert len(actual) == 12
    assert round(actual["1"], 2) == -815.0
    assert round(actual["2"], 2) == -824.0


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(name, id=f"properties_{name}")
        for name in (
            "incomes",
            "incomes_avg",
            "savings",
            "expenses_necessary",
            "expenses_free",
            "expenses_regular",
            "expenses_remains",
            "day_calced",
            "day_input",
            "remains",
            "month_len",
        )
    ],
)
def test_attribute_is_the_row_of_its_name(name, data):
    obj = PlanCalculateDaySum(data, 1)

    assert getattr(obj, name) == obj.get_row(name)


def test_attribute_of_an_unknown_name_raises(data):
    with pytest.raises(AttributeError):
        _ = PlanCalculateDaySum(data, 1).X


def test_rows_are_calculated_once(data):
    obj = PlanCalculateDaySum(data)
    _ = obj.month_len

    data.incomes = []

    assert obj.incomes_avg["1"] == 450


@pytest.fixture
def mock_db_services(mocker):
    base_path = "project.plans.lib.calc_day_sum"

    mocker.patch(f"{base_path}.IncomePlanModelService.summed_by_month", return_value=[])
    mocker.patch(
        f"{base_path}.ExpensePlanModelService.summed_by_month", return_value=[]
    )
    mocker.patch(f"{base_path}.SavingPlanModelService.summed_by_month", return_value=[])
    mocker.patch(f"{base_path}.DayPlanModelService.summed_by_month", return_value=[])
    mocker.patch(
        f"{base_path}.NecessaryPlanModelService.summed_by_month", return_value=[]
    )


def test_plan_collect_data_formats_month_len_as_tall_list(mock_db_services, mocker):
    mock_user = mocker.Mock()
    test_year = 2024

    obj = PlanCollectData(user=mock_user, year=test_year).get_data()
    actual_month_len = obj.month_len

    assert actual_month_len == MONTH_LEN
