from datetime import datetime
from types import SimpleNamespace

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.balance_rows import SavingBalanceRows
from .strategies import HAVE, TYPES, owner, rows, worth


def savings_table(incomes, expenses, have, types, moves=()):
    sources = SimpleNamespace(
        moves=moves, incomes=incomes, expenses=expenses, have=have, types=types
    )
    return SavingBalanceRows(sources).rows.collect().to_dicts()


def of_owner_1(rows):
    return [row for row in rows if row["category_id"] == 1]


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        {"year": 2000, "incomes": 100, "fee": 2, "category_id": 1},
        {"year": 2000, "incomes": 100, "fee": 2, "category_id": 1},
        {"year": 1999, "incomes": 50, "fee": 1, "category_id": 1},
        {"year": 1999, "incomes": 50, "fee": 1, "category_id": 1},
        {"year": 1999, "incomes": 55, "fee": 3, "category_id": 2},
        {"year": 1999, "incomes": 55, "fee": 3, "category_id": 2},
        {"year": 2000, "incomes": 110, "fee": 4, "category_id": 2},
        {"year": 2000, "incomes": 110, "fee": 4, "category_id": 2},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        {"year": 2000, "expenses": 50, "fee": 2, "category_id": 1},
        {"year": 2000, "expenses": 50, "fee": 2, "category_id": 1},
        {"year": 1999, "expenses": 25, "fee": 3, "category_id": 1},
        {"year": 1999, "expenses": 25, "fee": 3, "category_id": 1},
        {"year": 2000, "expenses": 55, "fee": 1, "category_id": 2},
        {"year": 2000, "expenses": 55, "fee": 1, "category_id": 2},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {
            "category_id": 1,
            "year": 1999,
            "have": 75,
            "latest_check": datetime(1999, 1, 1),
        },
        {
            "category_id": 1,
            "year": 2000,
            "have": 300,
            "latest_check": datetime(2000, 1, 2),
        },
        {
            "category_id": 2,
            "year": 1999,
            "have": 100,
            "latest_check": datetime(1999, 1, 3),
        },
        {
            "category_id": 2,
            "year": 2000,
            "have": 250,
            "latest_check": datetime(2000, 1, 4),
        },
    ]


@pytest.mark.parametrize(
    "extra_types, extra_incomes, extra_rows",
    [
        pytest.param([], [], {}, id="types"),
        pytest.param([owner(666)], [], {}, id="type_without_records"),
        pytest.param(
            [owner(666, closed=1999)],
            [{"year": 1974, "incomes": 10, "fee": 1, "category_id": 666}],
            {
                666: [
                    (1974, 10, 1, 0, 0, 10, 1),
                    *[(year, 10, 1, 10, 1, 0, 0) for year in range(1975, 2000)],
                ]
            },
            id="old_type",
        ),
    ],
)
def test_table_rows_of_each_type(extra_types, extra_incomes, extra_rows):
    incomes = [
        {"year": 1998, "incomes": 10, "fee": 1, "category_id": 1},
        {"year": 1998, "incomes": 20, "fee": 2, "category_id": 2},
        {"year": 1999, "incomes": 30, "fee": 3, "category_id": 1},
        *extra_incomes,
    ]
    columns = (
        "year",
        "incomes",
        "fee",
        "past_amount",
        "past_fee",
        "per_year_incomes",
        "per_year_fee",
    )
    actual = {}
    for row in savings_table(incomes, [], [], [*TYPES, *extra_types]):
        actual.setdefault(row["category_id"], []).append(
            tuple(row[column] for column in columns)
        )

    assert actual == {
        1: [
            (1998, 10, 1, 0, 0, 10, 1),
            (1999, 40, 4, 10, 1, 30, 3),
            (2000, 40, 4, 40, 4, 0, 0),
        ],
        2: [
            (1998, 20, 2, 0, 0, 20, 2),
            (1999, 20, 2, 20, 2, 0, 0),
            (2000, 20, 2, 20, 2, 0, 0),
        ],
        **extra_rows,
    }


@pytest.mark.parametrize(
    "given_inputs, expected",
    [
        pytest.param(
            ("incomes", "expenses", "have"),
            {
                "category_id": [1, 1, 1],
                "year": [1999, 2000, 2001],
                "past_amount": [0, 100, 300],
                "past_fee": [0, 2, 6],
                "fee": [2, 6, 6],
                "per_year_incomes": [100, 200, 0],
                "per_year_fee": [2, 4, 0],
                "sold": [50, 150, 150],
                "sold_fee": [6, 10, 10],
                "incomes": [100, 300, 300],
                "market_value": [75, 300, 300],
                "profit_sum": [23, 144, 144],
                "profit_proc": [23, 48, 48],
                "latest_check": [
                    datetime(1999, 1, 1),
                    datetime(2000, 1, 2),
                    datetime(2000, 1, 2),
                ],
            },
            id="incomes_expenses_and_have",
        ),
        pytest.param(
            ("expenses",),
            {
                "category_id": [1, 1, 1],
                "year": [1999, 2000, 2001],
                "past_amount": [0, 0, 0],
                "past_fee": [0, 0, 0],
                "fee": [0, 0, 0],
                "per_year_incomes": [0, 0, 0],
                "per_year_fee": [0, 0, 0],
                "sold": [50, 150, 150],
                "sold_fee": [6, 10, 10],
                "incomes": [0, 0, 0],
                "market_value": [0, 0, 0],
                "profit_sum": [50, 150, 150],
                "profit_proc": [0, 0, 0],
                "latest_check": [None] * 3,
            },
            id="expenses",
        ),
        pytest.param(
            ("incomes",),
            {
                "category_id": [1, 1, 1],
                "year": [1999, 2000, 2001],
                "past_amount": [0, 100, 300],
                "past_fee": [0, 2, 6],
                "fee": [2, 6, 6],
                "per_year_incomes": [100, 200, 0],
                "per_year_fee": [2, 4, 0],
                "sold": [0, 0, 0],
                "sold_fee": [0, 0, 0],
                "incomes": [100, 300, 300],
                "market_value": [0, 0, 0],
                "profit_sum": [-102, -306, -306],
                "profit_proc": [0, 0, 0],
                "latest_check": [None] * 3,
            },
            id="incomes",
        ),
        pytest.param(
            ("have",),
            {
                "category_id": [1, 1, 1],
                "year": [1999, 2000, 2001],
                "past_amount": [0, 0, 0],
                "past_fee": [0, 0, 0],
                "fee": [0, 0, 0],
                "per_year_incomes": [0, 0, 0],
                "per_year_fee": [0, 0, 0],
                "sold": [0, 0, 0],
                "sold_fee": [0, 0, 0],
                "incomes": [0, 0, 0],
                "market_value": [75, 300, 300],
                "profit_sum": [75, 300, 300],
                "profit_proc": [0, 0, 0],
                "latest_check": [
                    datetime(1999, 1, 1),
                    datetime(2000, 1, 2),
                    datetime(2000, 1, 2),
                ],
            },
            id="have",
        ),
        pytest.param((), {"category_id": [], "year": []}, id="nothing"),
    ],
)
def test_table_from_the_inputs_given(incomes, expenses, have, given_inputs, expected):
    inputs = {"incomes": incomes, "expenses": expenses, "have": have}
    actual = savings_table(
        types=TYPES,
        **{
            name: of_owner_1(given) if name in given_inputs else []
            for name, given in inputs.items()
        },
    )

    assert {column: [row[column] for row in actual] for column in expected} == expected


@pytest.mark.parametrize(
    "expenses, worth_in_close_year, expected",
    [
        pytest.param(
            [{"year": 2000, "expenses": 1, "fee": 20, "category_id": 1}],
            500,
            {
                "year": [1999, 2000],
                "market_value": [1200, 0],
                "sold": [0, 1],
                "sold_fee": [0, 20],
                "incomes": [1000, 1000],
                "fee": [10, 10],
                "profit_sum": [190, -1009],
                "profit_proc": [19, -100.9],
            },
            id="a_sell_reads_no_worth",
        ),
        pytest.param(
            [{"year": 1999, "expenses": 600, "fee": 20, "category_id": 1}],
            500,
            {
                "year": [1999, 2000],
                "market_value": [1200, 0],
                "sold": [600, 600],
                "sold_fee": [20, 20],
                "incomes": [1000, 1000],
                "fee": [10, 10],
                "profit_sum": [790, -410],
                "profit_proc": [79, -41],
            },
            id="a_sell_the_year_before_reads_no_worth",
        ),
        pytest.param(
            [],
            1300,
            {
                "year": [1999, 2000],
                "market_value": [1200, 1300],
                "sold": [0, 0],
                "sold_fee": [0, 0],
                "incomes": [1000, 1000],
                "fee": [10, 10],
                "profit_sum": [190, 290],
                "profit_proc": [19, 29],
            },
            id="no_sell_keeps_worth",
        ),
    ],
)
def test_table_close_year(expenses, worth_in_close_year, expected):
    incomes = [{"year": 1999, "incomes": 1000, "fee": 10, "category_id": 1}]
    have = [
        {"category_id": 1, "year": 1999, "have": 1200, "latest_check": None},
        {
            "category_id": 1,
            "year": 2000,
            "have": worth_in_close_year,
            "latest_check": None,
        },
    ]
    actual = savings_table(incomes, expenses, have, [owner(1, closed=2000)])

    assert {column: [row[column] for row in actual] for column in expected} == expected


ORDER_INCOMES = [
    {"year": year, "incomes": 10 * year % 7 + 1, "fee": 1, "category_id": pk}
    for pk in (1, 2, 3)
    for year in (1996, 1997, 1999, 2002)
]
ORDER_EXPENSES = [
    {"year": 1999, "expenses": 3, "fee": 1, "category_id": 2},
    {"year": 2002, "expenses": 4, "fee": 0, "category_id": 3},
]
ORDER_HAVE = [
    {"category_id": pk, "year": year, "have": pk * year % 50, "latest_check": dt}
    for pk in (1, 2, 3)
    for year, dt in ((1997, datetime(1997, 3, 1)), (2000, datetime(2000, 5, 1)))
]
ORDER_MOVES = [
    {"category_id": 2, "date": datetime(1999, 6, 1).date(), "price": 3},
    {"category_id": 3, "date": datetime(2002, 6, 1).date(), "price": 4},
]
ORDER_INPUT = (ORDER_INCOMES, ORDER_EXPENSES, ORDER_HAVE, TYPES, ORDER_MOVES)


@pytest.fixture(name="order_table", scope="module")
def fixture_order_table():
    return savings_table(*ORDER_INPUT)


@given(*(st.permutations(x) for x in ORDER_INPUT))
@example(*(x[::-1] for x in ORDER_INPUT))
def test_table_does_not_depend_on_the_input_row_order(
    order_table, incomes, expenses, have, types, moves
):
    actual = savings_table(incomes, expenses, have, types, moves)

    assert actual == order_table


@given(
    st.lists(rows("incomes", fee=st.integers(0, 1000)), min_size=1, max_size=12),
    st.lists(rows("expenses", fee=st.just(0)), max_size=12),
    HAVE,
)
def test_table_profit_is_worth_plus_sold_minus_incomes_and_fee(incomes, expenses, have):
    actual = savings_table(incomes, expenses, have, TYPES)

    def until(source, column, row):
        return sum(
            x[column]
            for x in source
            if x["category_id"] == row["category_id"] and x["year"] <= row["year"]
        )

    assert actual
    for row in actual:
        market_value = worth(have, row)

        assert row["incomes"] == until(incomes, "incomes", row)
        assert row["fee"] == until(incomes, "fee", row)
        assert row["sold"] == until(expenses, "expenses", row)
        assert row["market_value"] == market_value
        assert row["profit_sum"] == (
            market_value + row["sold"] - row["incomes"] - row["fee"]
        )
