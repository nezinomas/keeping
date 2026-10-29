from types import SimpleNamespace

import pytest

from ...lib.balance_rows import Accounts, Savings


@pytest.mark.parametrize("table", [Accounts, Savings])
def test_table_filtered_closed_categories(table):
    incomes = [
        {"year": 1999, "incomes": 50, "category_id": 1},
        {"year": 1999, "incomes": 55, "category_id": 2},
        {"year": 2000, "incomes": 110, "category_id": 2},
    ]

    types = [
        SimpleNamespace(pk=1, closed=1999),
        SimpleNamespace(pk=2, closed=None),
    ]
    data = SimpleNamespace(moves=[], incomes=incomes, expenses=[], have=[], types=types)
    actual = table(data).df.collect()

    assert actual["category_id"].to_list() == [1, 2, 2, 2]
    assert actual["year"].to_list() == [1999, 1999, 2000, 2001]


@pytest.mark.parametrize("table", [Accounts, Savings])
def test_table_of_rows_without_a_year_raises(table, types):
    incomes = [{"year": None, "incomes": 5, "fee": 1, "category_id": 1}]
    data = SimpleNamespace(moves=[], incomes=incomes, expenses=[], have=[], types=types)

    with pytest.raises(TypeError):
        table(data)
