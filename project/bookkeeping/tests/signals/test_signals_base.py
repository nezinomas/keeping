from types import SimpleNamespace

import pytest

from ...lib.balance_rows import AccountBalanceRows, SavingBalanceRows
from .strategies import owner


def sources(incomes, types):
    return SimpleNamespace(moves=[], incomes=incomes, expenses=[], have=[], types=types)


@pytest.mark.parametrize("table", [AccountBalanceRows, SavingBalanceRows])
def test_table_filtered_closed_categories(table):
    incomes = [
        {"year": 1999, "incomes": 50, "category_id": 1},
        {"year": 1999, "incomes": 55, "category_id": 2},
        {"year": 2000, "incomes": 110, "category_id": 2},
    ]
    actual = table(sources(incomes, [owner(1, closed=1999), owner(2)])).rows.collect()

    assert actual["category_id"].to_list() == [1, 2, 2, 2]
    assert actual["year"].to_list() == [1999, 1999, 2000, 2001]


@pytest.mark.parametrize("table", [AccountBalanceRows, SavingBalanceRows])
def test_table_of_entries_without_owners_raises(table):
    incomes = [{"year": 1999, "incomes": 5, "fee": 1, "category_id": 1}]

    with pytest.raises(ValueError, match="owners"):
        table(sources(incomes, []))
