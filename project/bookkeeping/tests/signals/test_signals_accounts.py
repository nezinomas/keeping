from datetime import datetime
from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ...lib.balance_rows import Accounts
from .strategies import HAVE, TYPES, rows, worth


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


def test_table(incomes, expenses, have, types):
    incomes.extend(
        [
            {"year": 1997, "incomes": 5, "category_id": 1},
            {"year": 1998, "incomes": 15, "category_id": 1},
        ]
    )
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have, types=types)
    actual = Accounts(data).df.collect().to_dicts()

    assert actual[0]["category_id"] == 1
    assert actual[0]["year"] == 1997
    assert actual[0]["past"] == 0
    assert actual[0]["incomes"] == 5
    assert actual[0]["expenses"] == 0
    assert actual[0]["balance"] == 5
    assert actual[0]["have"] == 0
    assert actual[0]["delta"] == -5
    assert not actual[0]["latest_check"]

    assert actual[1]["category_id"] == 1
    assert actual[1]["year"] == 1998
    assert actual[1]["past"] == 5
    assert actual[1]["incomes"] == 15
    assert actual[1]["expenses"] == 0
    assert actual[1]["balance"] == 20
    assert actual[1]["have"] == 0
    assert actual[1]["delta"] == -20
    assert not actual[1]["latest_check"]

    assert actual[2]["category_id"] == 1
    assert actual[2]["year"] == 1999
    assert actual[2]["past"] == 20
    assert actual[2]["incomes"] == 100
    assert actual[2]["expenses"] == 50
    assert actual[2]["balance"] == 70
    assert actual[2]["have"] == 10
    assert actual[2]["delta"] == -60
    assert actual[2]["latest_check"] == datetime(1999, 1, 1, 3, 2, 1)

    assert actual[3]["category_id"] == 1
    assert actual[3]["year"] == 2000
    assert actual[3]["past"] == 70
    assert actual[3]["incomes"] == 200
    assert actual[3]["expenses"] == 100
    assert actual[3]["balance"] == 170
    assert actual[3]["have"] == 15
    assert actual[3]["delta"] == -155
    assert actual[3]["latest_check"] == datetime(2000, 1, 4, 3, 2, 1)

    assert actual[4]["category_id"] == 1
    assert actual[4]["year"] == 2001
    assert actual[4]["past"] == 170
    assert actual[4]["incomes"] == 0
    assert actual[4]["expenses"] == 0
    assert actual[4]["balance"] == 170
    assert actual[4]["have"] == 15
    assert actual[4]["delta"] == -155
    assert actual[4]["latest_check"] == datetime(2000, 1, 4, 3, 2, 1)

    assert actual[5]["category_id"] == 2
    assert actual[5]["year"] == 1999
    assert actual[5]["past"] == 0
    assert actual[5]["incomes"] == 110
    assert actual[5]["expenses"] == 0
    assert actual[5]["balance"] == 110
    assert actual[5]["have"] == 20
    assert actual[5]["delta"] == -90
    assert actual[5]["latest_check"] == datetime(1999, 1, 2, 3, 2, 1)

    assert actual[6]["category_id"] == 2
    assert actual[6]["year"] == 2000
    assert actual[6]["past"] == 110
    assert actual[6]["incomes"] == 220
    assert actual[6]["expenses"] == 110
    assert actual[6]["balance"] == 220
    assert actual[6]["have"] == 25
    assert actual[6]["delta"] == -195
    assert actual[6]["latest_check"] == datetime(2000, 1, 6, 3, 2, 1)

    assert actual[7]["category_id"] == 2
    assert actual[7]["year"] == 2001
    assert actual[7]["past"] == 220
    assert actual[7]["incomes"] == 0
    assert actual[7]["expenses"] == 0
    assert actual[7]["balance"] == 220
    assert actual[7]["have"] == 25
    assert actual[7]["delta"] == -195
    assert actual[7]["latest_check"] == datetime(2000, 1, 6, 3, 2, 1)


def test_copy_have_and_latest_from_previous_year(types):
    have = [
        {
            "category_id": 1,
            "year": 1998,
            "have": 10,
            "latest_check": datetime(1998, 1, 1, 3, 2, 1),
        },
    ]
    incomes = [
        {"year": 1998, "incomes": 1, "category_id": 1},
        {"year": 1999, "incomes": 2, "category_id": 1},
        {"year": 1998, "incomes": 2, "category_id": 2},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=have, types=types)
    actual = Accounts(data).df.collect().to_dicts()

    assert actual[0] == {
        "category_id": 1,
        "year": 1998,
        "incomes": 1,
        "expenses": 0,
        "have": 10,
        "latest_check": datetime(1998, 1, 1, 3, 2, 1),
        "balance": 1,
        "past": 0,
        "delta": 9,
    }

    assert actual[1] == {
        "category_id": 1,
        "year": 1999,
        "incomes": 2,
        "expenses": 0,
        "have": 10,
        "latest_check": datetime(1998, 1, 1, 3, 2, 1),
        "balance": 3,
        "past": 1,
        "delta": 7,
    }

    assert actual[2] == {
        "category_id": 1,
        "year": 2000,
        "incomes": 0,
        "expenses": 0,
        "have": 10,
        "latest_check": datetime(1998, 1, 1, 3, 2, 1),
        "balance": 3,
        "past": 3,
        "delta": 7,
    }

    assert actual[3] == {
        "category_id": 2,
        "year": 1998,
        "incomes": 2,
        "expenses": 0,
        "have": 0,
        "latest_check": None,
        "balance": 2,
        "past": 0,
        "delta": -2,
    }

    assert actual[4] == {
        "category_id": 2,
        "year": 1999,
        "incomes": 0,
        "expenses": 0,
        "have": 0,
        "latest_check": None,
        "balance": 2,
        "past": 2,
        "delta": -2,
    }

    assert actual[5] == {
        "category_id": 2,
        "year": 2000,
        "incomes": 0,
        "expenses": 0,
        "have": 0,
        "latest_check": None,
        "balance": 2,
        "past": 2,
        "delta": -2,
    }


@pytest.mark.parametrize(
    "extra_types, extra_incomes, extra_rows",
    [
        pytest.param([], [], {}, id="types"),
        pytest.param(
            [SimpleNamespace(pk=666, closed=None)], [], {}, id="type_without_records"
        ),
        pytest.param(
            [SimpleNamespace(pk=666, closed=None)],
            [{"year": 1974, "incomes": 1, "category_id": 666}],
            {666: [(1974, 1, 0), *[(year, 0, 1) for year in range(1975, 2001)]]},
            id="old_type",
        ),
    ],
)
def test_table_rows_of_each_type(types, extra_types, extra_incomes, extra_rows):
    incomes = [
        {"year": 1998, "incomes": 1, "category_id": 1},
        {"year": 1998, "incomes": 2, "category_id": 2},
        {"year": 1999, "incomes": 3, "category_id": 1},
        *extra_incomes,
    ]
    data = SimpleNamespace(
        incomes=incomes, expenses=[], have=[], types=[*types, *extra_types]
    )
    actual = {}
    for row in Accounts(data).df.collect().to_dicts():
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
            ("incomes", "expenses"),
            {
                "category_id": [1, 1, 1, 2, 2, 2],
                "year": [1999, 2000, 2001, 1999, 2000, 2001],
                "past": [0, 50, 150, 0, 110, 220],
                "incomes": [100, 200, 0, 110, 220, 0],
                "expenses": [50, 100, 0, 0, 110, 0],
                "balance": [50, 150, 150, 110, 220, 220],
                "have": [0, 0, 0, 0, 0, 0],
                "delta": [-50, -150, -150, -110, -220, -220],
                "latest_check": [None] * 6,
            },
            id="incomes_and_expenses",
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
def test_table_from_the_inputs_given(
    incomes, expenses, have, types, given_inputs, expected
):
    inputs = {"incomes": incomes, "expenses": expenses, "have": have}
    data = SimpleNamespace(
        types=types,
        **{
            name: given if name in given_inputs else []
            for name, given in inputs.items()
        },
    )
    actual = Accounts(data).df.collect()

    assert {column: actual[column].to_list() for column in expected} == expected


@given(
    st.lists(rows("incomes"), min_size=1, max_size=12),
    st.lists(rows("expenses"), max_size=12),
    HAVE,
)
def test_table_year_balance_follows_the_year_before(incomes, expenses, have):
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have, types=TYPES)
    actual = Accounts(data).df.collect().to_dicts()
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
