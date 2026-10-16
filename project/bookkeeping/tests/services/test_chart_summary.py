from datetime import date
from types import SimpleNamespace

import pytest

from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ...services.chart_summary import Charts, Data

TODAY = date(1999, 1, 1)


@pytest.mark.django_db
def test_data_salary_keeps_only_salary_incomes(main_user):
    salary = IncomeTypeFactory(title="Alga", type="salary")
    other = IncomeTypeFactory(title="Kita", type="other")
    IncomeFactory(date=date(1999, 1, 1), price=10, income_type=salary)
    IncomeFactory(date=date(1999, 2, 1), price=5, income_type=salary)
    IncomeFactory(date=date(1999, 3, 1), price=100, income_type=other)

    actual = [(x["year"], x["sum"]) for x in Data(main_user).salary]

    assert actual == [(1999, 15)]


@pytest.fixture(name="incomes_types")
def fixture_incomes_types():
    return [
        {"date": date(1998, 1, 1), "sum": 1, "title": "T1"},
        {"date": date(2000, 1, 1), "sum": 2, "title": "T1"},
        {"date": date(1999, 1, 1), "sum": 3, "title": "T2"},
        {"date": date(2000, 1, 1), "sum": 4, "title": "T2"},
    ]


def test_chart_incomes_context():
    data = SimpleNamespace(
        incomes=[{"sum": 24, "year": 1998}],
        incomes_types=[],
        salary=[
            {"sum": 12, "year": 1998},
        ],
        expenses=[],
    )
    actual = Charts(data).chart_incomes(TODAY)

    assert actual == {
        "records": 1,
        "chart_title": "Pajamos",
        "categories": [1998],
        "incomes": [2],
        "incomes_title": "Vidutinės pajamos",
        "salary": [1],
        "salary_title": "Vidutinis atlyginimas, €",
    }


def _incomes(incomes, salary):
    data = SimpleNamespace(
        salary=salary, incomes=incomes, incomes_types=[], expenses=[]
    )
    return Charts(data).chart_incomes(TODAY)


@pytest.mark.parametrize(
    "incomes, salary, key, expect",
    [
        pytest.param(
            [],
            [{"sum": 12, "year": 1998}, {"sum": 10, "year": 1999}],
            "categories",
            [1998, 1999],
            id="salary_years",
        ),
        pytest.param(
            [],
            [{"sum": 12, "year": 1998}, {"sum": 10, "year": 1999}],
            "salary",
            [1, 10],
            id="salary",
        ),
        pytest.param(
            [{"sum": 24, "year": 1998}, {"sum": 12, "year": 1999}],
            [{"sum": 12, "year": 1998}, {"sum": 10, "year": 1999}],
            "incomes",
            [2, 12],
            id="incomes",
        ),
        pytest.param(
            [{"sum": 12, "year": 1999}],
            [{"sum": 10, "year": 1999}],
            "records",
            1,
            id="records",
        ),
    ],
)
def test_chart_incomes(incomes, salary, key, expect):
    actual = _incomes(incomes, salary)[key]

    assert actual == expect


def test_chart_incomes_records_no_data():
    data = SimpleNamespace(incomes=[], incomes_types=[], salary=[], expenses=[])
    actual = Charts(data).chart_incomes(TODAY)

    assert actual == {"records": 0}


def _balance(incomes, expenses):
    data = SimpleNamespace(
        salary=[], incomes=incomes, incomes_types=[], expenses=expenses
    )
    return Charts(data).chart_balance()


def test_chart_balance_context():
    actual = _balance([{"sum": 12, "year": 1998}], [])

    assert actual == {
        "records": 1,
        "chart_title": "Pajamos ir išlaidos",
        "categories": [1998],
        "incomes": [12],
        "incomes_title": "Pajamos",
        "expenses": [],
        "expenses_title": "Išlaidos",
    }


def test_chart_balance_no_data():
    actual = _balance([], [])

    assert actual == {"records": 0}


Y98 = {"sum": 12, "year": 1998}
Y99 = {"sum": 24, "year": 1999}
Y00 = {"sum": 12, "year": 2000}


@pytest.mark.parametrize(
    "incomes, expenses, expect",
    [
        pytest.param([Y98], [], 1, id="only_incomes"),
        pytest.param([], [Y98], 1, id="only_expenses"),
        pytest.param([Y98], [Y98, Y99], 1, id="incomes_win_over_expenses"),
    ],
)
def test_chart_balance_records(incomes, expenses, expect):
    actual = _balance(incomes, expenses)["records"]

    assert actual == expect


@pytest.mark.parametrize(
    "incomes, expenses",
    [
        pytest.param([Y98, Y99], [], id="only_incomes"),
        pytest.param([], [Y98, Y99], id="only_expenses"),
        pytest.param([Y98, Y99], [Y00], id="incomes_win_over_expenses"),
    ],
)
def test_chart_balance_categories(incomes, expenses):
    actual = _balance(incomes, expenses)["categories"]

    assert actual == [1998, 1999]


@pytest.mark.parametrize(
    "incomes, expenses, key",
    [
        pytest.param([Y98, Y99], [], "incomes", id="incomes"),
        pytest.param([], [Y98, Y99], "expenses", id="expenses"),
    ],
)
def test_chart_balance_sums(incomes, expenses, key):
    actual = _balance(incomes, expenses)[key]

    assert actual == [12, 24]


def test_chart_incomes_types_context(incomes_types):
    data = SimpleNamespace(
        incomes=[], salary=[], expenses=[], incomes_types=incomes_types
    )
    actual = Charts(data).chart_incomes_types()

    assert actual == {
        "chart_title": "Pajamos",
        "categories": [1998, 1999, 2000],
        "data": [
            {"name": "T1", "data": [1, 0, 2]},
            {"name": "T2", "data": [0, 3, 4]},
        ],
    }


def test_chart_incomes_types_categories_no_data():
    data = SimpleNamespace(incomes=[], salary=[], expenses=[], incomes_types=[])
    actual = Charts(data).chart_incomes_types()

    assert actual["categories"] == []


def test_chart_incomes_types_categories(incomes_types):
    data = SimpleNamespace(
        incomes=[], salary=[], expenses=[], incomes_types=incomes_types
    )
    actual = Charts(data).chart_incomes_types()

    assert actual["categories"] == [1998, 1999, 2000]


def test_chart_incomes_types_data(incomes_types):
    data = SimpleNamespace(
        incomes=[], salary=[], expenses=[], incomes_types=incomes_types
    )
    actual = Charts(data).chart_incomes_types()

    assert actual["data"][0] == {"name": "T1", "data": [1, 0, 2]}
    assert actual["data"][1] == {"name": "T2", "data": [0, 3, 4]}


def test_chart_incomes_types_data_no_data():
    data = SimpleNamespace(incomes=[], salary=[], expenses=[], incomes_types=[])
    actual = Charts(data).chart_incomes_types()

    assert actual["data"] == []
