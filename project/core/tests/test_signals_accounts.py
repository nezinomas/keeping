from datetime import datetime
from types import SimpleNamespace

import pytest
import time_machine

from ..lib.signals import Accounts


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


@pytest.fixture(name="types")
def fixture_types():
    return [
        SimpleNamespace(pk=1, closed=None),
        SimpleNamespace(pk=2, closed=None),
    ]


@time_machine.travel("2000-12-31")
def test_table(incomes, expenses, have, types):
    incomes.extend(
        [
            {"year": 1997, "incomes": 5, "category_id": 1},
            {"year": 1998, "incomes": 15, "category_id": 1},
        ]
    )
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have, types=types)
    actual = Accounts(data).table

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

    # future year=2001
    assert actual[4]["category_id"] == 1
    assert actual[4]["year"] == 2001
    assert actual[4]["past"] == 170
    assert actual[4]["incomes"] == 0
    assert actual[4]["expenses"] == 0
    assert actual[4]["balance"] == 170
    assert actual[4]["have"] == 15
    assert actual[4]["delta"] == -155
    assert actual[4]["latest_check"] == datetime(2000, 1, 4, 3, 2, 1)

    # second account
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

    # future year=2001
    assert actual[7]["category_id"] == 2
    assert actual[7]["year"] == 2001
    assert actual[7]["past"] == 220
    assert actual[7]["incomes"] == 0
    assert actual[7]["expenses"] == 0
    assert actual[7]["balance"] == 220
    assert actual[7]["have"] == 25
    assert actual[7]["delta"] == -195
    assert actual[7]["latest_check"] == datetime(2000, 1, 6, 3, 2, 1)


@time_machine.travel("2000-12-31")
def test_year_category_id_set(incomes, expenses, have, types):
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have, types=types)
    actual = Accounts(data).year_category_id_set

    assert actual == {
        (1999, 1),
        (2000, 1),
        (2001, 1),
        (1999, 2),
        (2000, 2),
        (2001, 2),
    }


@time_machine.travel("1997-12-31")
def test_table_one_record(types):
    incomes = [{"year": 1997, "incomes": 5, "category_id": 1}]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

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
    assert actual[1]["incomes"] == 0
    assert actual[1]["expenses"] == 0
    assert actual[1]["balance"] == 5
    assert actual[1]["have"] == 0
    assert actual[1]["delta"] == -5
    assert not actual[1]["latest_check"]


@time_machine.travel("1999-1-1")
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
    actual = Accounts(data).table

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


@time_machine.travel("1999-1-1")
def test_table_with_types(types):
    incomes = [
        {"year": 1998, "incomes": 1, "category_id": 1},
        {"year": 1998, "incomes": 2, "category_id": 2},
        {"year": 1999, "incomes": 3, "category_id": 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 1998
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 2

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 1999
    assert actual[4]["past"] == 2
    assert actual[4]["incomes"] == 0


@time_machine.travel("1999-1-1")
def test_table_type_without_recods(types):
    types.append(SimpleNamespace(pk=666))
    incomes = [
        {"year": 1998, "incomes": 1, "category_id": 1},
        {"year": 1998, "incomes": 2, "category_id": 2},
        {"year": 1999, "incomes": 3, "category_id": 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 1998
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 2

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 1999
    assert actual[4]["past"] == 2
    assert actual[4]["incomes"] == 0


@time_machine.travel("1999-1-1")
def test_table_old_type(types):
    types.append(SimpleNamespace(pk=666))
    incomes = [
        {"year": 1974, "incomes": 1, "category_id": 666},
        {"year": 1998, "incomes": 1, "category_id": 1},
        {"year": 1998, "incomes": 2, "category_id": 2},
        {"year": 1999, "incomes": 3, "category_id": 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 1998
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 2

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 1999
    assert actual[4]["past"] == 2
    assert actual[4]["incomes"] == 0


@time_machine.travel("2000-12-31")
def test_table_have_empty(incomes, expenses, types):
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=[], types=types)
    actual = Accounts(data).table

    assert actual[0]["category_id"] == 1
    assert actual[0]["year"] == 1999
    assert actual[0]["past"] == 0
    assert actual[0]["incomes"] == 100
    assert actual[0]["expenses"] == 50
    assert actual[0]["balance"] == 50
    assert actual[0]["have"] == 0
    assert actual[0]["delta"] == -50
    assert not actual[0]["latest_check"]

    assert actual[1]["category_id"] == 1
    assert actual[1]["year"] == 2000
    assert actual[1]["past"] == 50
    assert actual[1]["incomes"] == 200
    assert actual[1]["expenses"] == 100
    assert actual[1]["balance"] == 150
    assert actual[1]["have"] == 0
    assert actual[1]["delta"] == -150
    assert not actual[1]["latest_check"]

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 1999
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 110
    assert actual[3]["expenses"] == 0
    assert actual[3]["balance"] == 110
    assert actual[3]["have"] == 0
    assert actual[3]["delta"] == -110
    assert not actual[3]["latest_check"]

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 2000
    assert actual[4]["past"] == 110
    assert actual[4]["incomes"] == 220
    assert actual[4]["expenses"] == 110
    assert actual[4]["balance"] == 220
    assert actual[4]["have"] == 0
    assert actual[4]["delta"] == -220
    assert not actual[4]["latest_check"]


@time_machine.travel("2000-12-31")
def test_table_incomes_empty(expenses, types):
    data = SimpleNamespace(incomes=[], expenses=expenses, have=[], types=types)
    actual = Accounts(data).table

    assert actual[0]["category_id"] == 1
    assert actual[0]["year"] == 1999
    assert actual[0]["past"] == 0
    assert actual[0]["incomes"] == 0
    assert actual[0]["expenses"] == 50
    assert actual[0]["balance"] == -50
    assert actual[0]["have"] == 0
    assert actual[0]["delta"] == 50
    assert not actual[0]["latest_check"]

    assert actual[1]["category_id"] == 1
    assert actual[1]["year"] == 2000
    assert actual[1]["past"] == -50
    assert actual[1]["incomes"] == 0
    assert actual[1]["expenses"] == 100
    assert actual[1]["balance"] == -150
    assert actual[1]["have"] == 0
    assert actual[1]["delta"] == 150
    assert not actual[1]["latest_check"]

    assert actual[2]["category_id"] == 1
    assert actual[2]["year"] == 2001
    assert actual[2]["past"] == -150
    assert actual[2]["incomes"] == 0
    assert actual[2]["expenses"] == 0
    assert actual[2]["balance"] == -150
    assert actual[2]["have"] == 0
    assert actual[2]["delta"] == 150
    assert not actual[2]["latest_check"]

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 2000
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 0
    assert actual[3]["expenses"] == 110
    assert actual[3]["balance"] == -110
    assert actual[3]["have"] == 0
    assert actual[3]["delta"] == 110
    assert not actual[3]["latest_check"]

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 2001
    assert actual[4]["past"] == -110
    assert actual[4]["incomes"] == 0
    assert actual[4]["expenses"] == 0
    assert actual[4]["balance"] == -110
    assert actual[4]["have"] == 0
    assert actual[4]["delta"] == 110
    assert not actual[4]["latest_check"]


@time_machine.travel("2000-12-31")
def test_table_expenses_empty(incomes, types):
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[0]["category_id"] == 1
    assert actual[0]["year"] == 1999
    assert actual[0]["past"] == 0
    assert actual[0]["incomes"] == 100
    assert actual[0]["expenses"] == 0
    assert actual[0]["balance"] == 100
    assert actual[0]["have"] == 0
    assert actual[0]["delta"] == -100
    assert not actual[0]["latest_check"]

    assert actual[1]["category_id"] == 1
    assert actual[1]["year"] == 2000
    assert actual[1]["past"] == 100
    assert actual[1]["incomes"] == 200
    assert actual[1]["expenses"] == 0
    assert actual[1]["balance"] == 300
    assert actual[1]["have"] == 0
    assert actual[1]["delta"] == -300
    assert not actual[1]["latest_check"]

    assert actual[2]["category_id"] == 1
    assert actual[2]["year"] == 2001
    assert actual[2]["past"] == 300
    assert actual[2]["incomes"] == 0
    assert actual[2]["expenses"] == 0
    assert actual[2]["balance"] == 300
    assert actual[2]["have"] == 0
    assert actual[2]["delta"] == -300
    assert not actual[2]["latest_check"]

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 1999
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 110
    assert actual[3]["expenses"] == 0
    assert actual[3]["balance"] == 110
    assert actual[3]["have"] == 0
    assert actual[3]["delta"] == -110
    assert not actual[3]["latest_check"]

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 2000
    assert actual[4]["past"] == 110
    assert actual[4]["incomes"] == 220
    assert actual[4]["expenses"] == 0
    assert actual[4]["balance"] == 330
    assert actual[4]["have"] == 0
    assert actual[4]["delta"] == -330
    assert not actual[4]["latest_check"]

    assert actual[5]["category_id"] == 2
    assert actual[5]["year"] == 2001
    assert actual[5]["past"] == 330
    assert actual[5]["incomes"] == 0
    assert actual[5]["expenses"] == 0
    assert actual[5]["balance"] == 330
    assert actual[5]["have"] == 0
    assert actual[5]["delta"] == -330
    assert not actual[5]["latest_check"]


def test_table_incomes_expenses_empty(types):
    data = SimpleNamespace(incomes=[], expenses=[], have=[], types=types)
    actual = Accounts(data).table

    expect = []

    assert actual == expect


@time_machine.travel("2000-12-31")
def test_table_only_have(have, types):
    data = SimpleNamespace(incomes=[], expenses=[], have=have, types=types)
    actual = Accounts(data).table

    assert actual[0]["category_id"] == 1
    assert actual[0]["year"] == 1999
    assert actual[0]["past"] == 0
    assert actual[0]["incomes"] == 0
    assert actual[0]["expenses"] == 0
    assert actual[0]["balance"] == 0
    assert actual[0]["have"] == 10
    assert actual[0]["delta"] == 10
    assert actual[0]["latest_check"] == datetime(1999, 1, 1, 3, 2, 1)

    assert actual[1]["category_id"] == 1
    assert actual[1]["year"] == 2000
    assert actual[1]["past"] == 0
    assert actual[1]["incomes"] == 0
    assert actual[1]["expenses"] == 0
    assert actual[1]["balance"] == 0
    assert actual[1]["have"] == 15
    assert actual[1]["delta"] == 15
    assert actual[1]["latest_check"] == datetime(2000, 1, 4, 3, 2, 1)

    assert actual[2]["category_id"] == 1
    assert actual[2]["year"] == 2001
    assert actual[2]["past"] == 0
    assert actual[2]["incomes"] == 0
    assert actual[2]["expenses"] == 0
    assert actual[2]["balance"] == 0
    assert actual[2]["have"] == 15
    assert actual[2]["delta"] == 15
    assert actual[2]["latest_check"] == datetime(2000, 1, 4, 3, 2, 1)

    assert actual[3]["category_id"] == 2
    assert actual[3]["year"] == 1999
    assert actual[3]["past"] == 0
    assert actual[3]["incomes"] == 0
    assert actual[3]["expenses"] == 0
    assert actual[3]["balance"] == 0
    assert actual[3]["have"] == 20
    assert actual[3]["delta"] == 20
    assert actual[3]["latest_check"] == datetime(1999, 1, 2, 3, 2, 1)

    assert actual[4]["category_id"] == 2
    assert actual[4]["year"] == 2000
    assert actual[4]["past"] == 0
    assert actual[4]["incomes"] == 0
    assert actual[4]["expenses"] == 0
    assert actual[4]["balance"] == 0
    assert actual[4]["have"] == 25
    assert actual[4]["delta"] == 25
    assert actual[4]["latest_check"] == datetime(2000, 1, 6, 3, 2, 1)

    assert actual[5]["category_id"] == 2
    assert actual[5]["year"] == 2001
    assert actual[5]["past"] == 0
    assert actual[5]["incomes"] == 0
    assert actual[5]["expenses"] == 0
    assert actual[5]["balance"] == 0
    assert actual[5]["have"] == 25
    assert actual[5]["delta"] == 25
    assert actual[5]["latest_check"] == datetime(2000, 1, 6, 3, 2, 1)
