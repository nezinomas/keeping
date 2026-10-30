from datetime import datetime
from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ...lib.balance_rows import AccountBalanceRows
from .strategies import HAVE, TYPES, owner, rows, worth


def accounts_table(incomes, expenses, have, types):
    sources = SimpleNamespace(
        incomes=incomes, expenses=expenses, have=have, types=types
    )
    return AccountBalanceRows(sources).rows.collect().to_dicts()


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        {"year": 1999, "incomes": 50, "category_id": 1},
        {"year": 1999, "incomes": 50, "category_id": 1},
        {"year": 2000, "incomes": 100, "category_id": 1},
        {"year": 2000, "incomes": 100, "category_id": 1},
        {"year": 1999, "incomes": 55, "category_id": 2},
        {"year": 1999, "incomes": 55, "category_id": 2},
        {"year": 2000, "incomes": 110, "category_id": 2},
        {"year": 2000, "incomes": 110, "category_id": 2},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        {"year": 1999, "expenses": 25, "category_id": 1},
        {"year": 1999, "expenses": 25, "category_id": 1},
        {"year": 2000, "expenses": 50, "category_id": 1},
        {"year": 2000, "expenses": 50, "category_id": 1},
        {"year": 2000, "expenses": 55, "category_id": 2},
        {"year": 2000, "expenses": 55, "category_id": 2},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {
            "category_id": 1,
            "year": 1999,
            "have": 10,
            "latest_check": datetime(1999, 1, 1, 3, 2, 1),
        },
        {
            "category_id": 1,
            "year": 2000,
            "have": 15,
            "latest_check": datetime(2000, 1, 4, 3, 2, 1),
        },
        {
            "category_id": 2,
            "year": 1999,
            "have": 20,
            "latest_check": datetime(1999, 1, 2, 3, 2, 1),
        },
        {
            "category_id": 2,
            "year": 2000,
            "have": 25,
            "latest_check": datetime(2000, 1, 6, 3, 2, 1),
        },
    ]


@pytest.mark.parametrize(
    "extra_types, extra_incomes, extra_rows",
    [
        pytest.param([], [], {}, id="types"),
        pytest.param([owner(666)], [], {}, id="type_without_records"),
        pytest.param(
            [owner(666)],
            [{"year": 1974, "incomes": 1, "category_id": 666}],
            {666: [(1974, 1, 0), *[(year, 0, 1) for year in range(1975, 2001)]]},
            id="old_type",
        ),
    ],
)
def test_table_rows_of_each_type(extra_types, extra_incomes, extra_rows):
    incomes = [
        {"year": 1998, "incomes": 1, "category_id": 1},
        {"year": 1998, "incomes": 2, "category_id": 2},
        {"year": 1999, "incomes": 3, "category_id": 1},
        *extra_incomes,
    ]
    actual = {}
    for row in accounts_table(incomes, [], [], [*TYPES, *extra_types]):
        actual.setdefault(row["category_id"], []).append(
            (row["year"], row["incomes"], row["past"])
        )

    assert actual == {
        1: [(1998, 1, 0), (1999, 3, 1), (2000, 0, 4)],
        2: [(1998, 2, 0), (1999, 0, 2), (2000, 0, 2)],
        **extra_rows,
    }


@pytest.mark.parametrize(
    "given_inputs, expected",
    [
        pytest.param(
            ("incomes", "expenses", "have"),
            {
                "category_id": [1, 1, 1, 2, 2, 2],
                "year": [1999, 2000, 2001, 1999, 2000, 2001],
                "past": [0, 50, 150, 0, 110, 220],
                "incomes": [100, 200, 0, 110, 220, 0],
                "expenses": [50, 100, 0, 0, 110, 0],
                "balance": [50, 150, 150, 110, 220, 220],
                "have": [10, 15, 15, 20, 25, 25],
                "delta": [-40, -135, -135, -90, -195, -195],
                "latest_check": [
                    datetime(1999, 1, 1, 3, 2, 1),
                    datetime(2000, 1, 4, 3, 2, 1),
                    datetime(2000, 1, 4, 3, 2, 1),
                    datetime(1999, 1, 2, 3, 2, 1),
                    datetime(2000, 1, 6, 3, 2, 1),
                    datetime(2000, 1, 6, 3, 2, 1),
                ],
            },
            id="incomes_expenses_and_have",
        ),
        pytest.param(
            ("expenses",),
            {
                "category_id": [1, 1, 1, 2, 2],
                "year": [1999, 2000, 2001, 2000, 2001],
                "past": [0, -50, -150, 0, -110],
                "incomes": [0, 0, 0, 0, 0],
                "expenses": [50, 100, 0, 110, 0],
                "balance": [-50, -150, -150, -110, -110],
                "have": [0, 0, 0, 0, 0],
                "delta": [50, 150, 150, 110, 110],
                "latest_check": [None] * 5,
            },
            id="expenses",
        ),
        pytest.param(
            ("incomes",),
            {
                "category_id": [1, 1, 1, 2, 2, 2],
                "year": [1999, 2000, 2001, 1999, 2000, 2001],
                "past": [0, 100, 300, 0, 110, 330],
                "incomes": [100, 200, 0, 110, 220, 0],
                "expenses": [0, 0, 0, 0, 0, 0],
                "balance": [100, 300, 300, 110, 330, 330],
                "have": [0, 0, 0, 0, 0, 0],
                "delta": [-100, -300, -300, -110, -330, -330],
                "latest_check": [None] * 6,
            },
            id="incomes",
        ),
        pytest.param(
            ("have",),
            {
                "category_id": [1, 1, 1, 2, 2, 2],
                "year": [1999, 2000, 2001, 1999, 2000, 2001],
                "past": [0, 0, 0, 0, 0, 0],
                "incomes": [0, 0, 0, 0, 0, 0],
                "expenses": [0, 0, 0, 0, 0, 0],
                "balance": [0, 0, 0, 0, 0, 0],
                "have": [10, 15, 15, 20, 25, 25],
                "delta": [10, 15, 15, 20, 25, 25],
                "latest_check": [
                    datetime(1999, 1, 1, 3, 2, 1),
                    datetime(2000, 1, 4, 3, 2, 1),
                    datetime(2000, 1, 4, 3, 2, 1),
                    datetime(1999, 1, 2, 3, 2, 1),
                    datetime(2000, 1, 6, 3, 2, 1),
                    datetime(2000, 1, 6, 3, 2, 1),
                ],
            },
            id="have",
        ),
        pytest.param((), {"category_id": [], "year": []}, id="nothing"),
    ],
)
def test_table_from_the_inputs_given(incomes, expenses, have, given_inputs, expected):
    inputs = {"incomes": incomes, "expenses": expenses, "have": have}
    actual = accounts_table(
        types=TYPES,
        **{
            name: given if name in given_inputs else []
            for name, given in inputs.items()
        },
    )

    assert {column: [row[column] for row in actual] for column in expected} == expected


@given(
    st.lists(rows("incomes"), min_size=1, max_size=12),
    st.lists(rows("expenses"), max_size=12),
    HAVE,
)
def test_table_year_balance_follows_the_year_before(incomes, expenses, have):
    actual = accounts_table(incomes, expenses, have, TYPES)
    previous = {}

    def total(source, column, row):
        return sum(
            x[column]
            for x in source
            if x["category_id"] == row["category_id"] and x["year"] == row["year"]
        )

    assert actual
    for row in actual:
        before = previous.get(
            row["category_id"], {"year": row["year"] - 1, "balance": 0}
        )

        assert row["year"] == before["year"] + 1
        assert row["incomes"] == total(incomes, "incomes", row)
        assert row["expenses"] == total(expenses, "expenses", row)
        assert row["have"] == worth(have, row)
        assert row["past"] == before["balance"]
        assert row["balance"] == row["past"] + row["incomes"] - row["expenses"]
        assert row["delta"] == row["have"] - row["balance"]
        previous[row["category_id"]] = row
