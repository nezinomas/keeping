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


INCOMES_TITLES = {
    "chart_title": "Pajamos",
    "incomes_title": "Vidutinės pajamos",
    "salary_title": "Vidutinis atlyginimas, €",
}
BALANCE_TITLES = {
    "chart_title": "Pajamos ir išlaidos",
    "incomes_title": "Pajamos",
    "expenses_title": "Išlaidos",
}
Y98 = {"sum": 12, "year": 1998}
Y99 = {"sum": 24, "year": 1999}
Y00 = {"sum": 12, "year": 2000}


@pytest.mark.parametrize(
    "incomes, salary, expect",
    [
        pytest.param(
            [{"sum": 24, "year": 1998}],
            [{"sum": 12, "year": 1998}],
            INCOMES_TITLES
            | {"records": 1, "categories": [1998], "incomes": [2], "salary": [1]},
            id="one_year",
        ),
        pytest.param(
            [],
            [{"sum": 12, "year": 1998}, {"sum": 10, "year": 1999}],
            INCOMES_TITLES
            | {
                "records": 2,
                "categories": [1998, 1999],
                "incomes": [],
                "salary": [1, 10],
            },
            id="salary_years_without_incomes",
        ),
        pytest.param(
            [{"sum": 24, "year": 1998}, {"sum": 12, "year": 1999}],
            [{"sum": 12, "year": 1998}, {"sum": 10, "year": 1999}],
            INCOMES_TITLES
            | {
                "records": 2,
                "categories": [1998, 1999],
                "incomes": [2, 12],
                "salary": [1, 10],
            },
            id="two_years",
        ),
        pytest.param(
            [{"sum": 12, "year": 1999}],
            [{"sum": 10, "year": 1999}],
            INCOMES_TITLES
            | {"records": 1, "categories": [1999], "incomes": [12], "salary": [10]},
            id="current_year",
        ),
        pytest.param([], [], {"records": 0}, id="no_data"),
    ],
)
def test_chart_incomes_context(incomes, salary, expect):
    data = SimpleNamespace(
        salary=salary, incomes=incomes, incomes_types=[], expenses=[]
    )
    actual = Charts(data).chart_incomes(TODAY)

    assert actual == expect


@pytest.mark.parametrize(
    "incomes, expenses, expect",
    [
        pytest.param(
            [Y98],
            [],
            BALANCE_TITLES
            | {"records": 1, "categories": [1998], "incomes": [12], "expenses": []},
            id="one_year",
        ),
        pytest.param(
            [Y98, Y99],
            [],
            BALANCE_TITLES
            | {
                "records": 2,
                "categories": [1998, 1999],
                "incomes": [12, 24],
                "expenses": [],
            },
            id="only_incomes",
        ),
        pytest.param(
            [],
            [Y98, Y99],
            BALANCE_TITLES
            | {
                "records": 2,
                "categories": [1998, 1999],
                "incomes": [],
                "expenses": [12, 24],
            },
            id="only_expenses",
        ),
        pytest.param(
            [Y98, Y99],
            [Y00],
            BALANCE_TITLES
            | {
                "records": 2,
                "categories": [1998, 1999],
                "incomes": [12, 24],
                "expenses": [12],
            },
            id="incomes_win_over_fewer_expenses",
        ),
        pytest.param(
            [Y98],
            [Y98, Y99],
            BALANCE_TITLES
            | {
                "records": 1,
                "categories": [1998],
                "incomes": [12],
                "expenses": [12, 24],
            },
            id="incomes_win_over_more_expenses",
        ),
        pytest.param([], [], {"records": 0}, id="no_data"),
    ],
)
def test_chart_balance_context(incomes, expenses, expect):
    data = SimpleNamespace(
        salary=[], incomes=incomes, incomes_types=[], expenses=expenses
    )
    actual = Charts(data).chart_balance()

    assert actual == expect


@pytest.mark.parametrize(
    "incomes_types, expect",
    [
        pytest.param(
            [
                {"date": date(1998, 1, 1), "sum": 1, "title": "T1"},
                {"date": date(2000, 1, 1), "sum": 2, "title": "T1"},
                {"date": date(1999, 1, 1), "sum": 3, "title": "T2"},
                {"date": date(2000, 1, 1), "sum": 4, "title": "T2"},
            ],
            {
                "chart_title": "Pajamos",
                "categories": [1998, 1999, 2000],
                "data": [
                    {"name": "T1", "data": [1, 0, 2]},
                    {"name": "T2", "data": [0, 3, 4]},
                ],
            },
            id="two_types",
        ),
        pytest.param(
            [],
            {"chart_title": "Pajamos", "categories": [], "data": []},
            id="no_data",
        ),
    ],
)
def test_chart_incomes_types_context(incomes_types, expect):
    data = SimpleNamespace(
        incomes=[], salary=[], expenses=[], incomes_types=incomes_types
    )
    actual = Charts(data).chart_incomes_types()

    assert actual == expect
