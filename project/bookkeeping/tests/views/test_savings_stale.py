from datetime import date

import pytest

from ....savings.tests.factories import SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ....users.models import User
from ..helper import row_cells, stale_fund, tab_table, total_cells, view_queries
from ..signals.helpers import YEAR, buy, sell, worth

pytestmark = pytest.mark.django_db

TABLES = [
    pytest.param("Fondai", "funds", id="funds"),
    pytest.param("Pensijos", "pensions", id="pensions"),
]


def _table(client, title="Fondai"):
    return tab_table(client, "bookkeeping:tab_funds", title)


@pytest.mark.parametrize("title, kind", TABLES)
def test_a_stale_worth_shows_dashes_in_the_profit_cells(client_logged, title, kind):
    stale_fund(kind=kind)

    cells = row_cells(_table(client_logged, title), "Stale")

    assert cells[9] == "1.000,00"
    assert cells[10:12] == ["-", "-"]


def test_a_stale_worth_shows_dashes_the_next_year_too(client_logged):
    stale_fund()
    User.objects.update(year=YEAR + 1)

    cells = row_cells(_table(client_logged), "Stale")

    assert cells[10:12] == ["-", "-"]


def test_a_worth_dated_after_the_sell_shows_the_profit(client_logged):
    fund = stale_fund()
    worth(fund, 70000)

    cells = row_cells(_table(client_logged), "Stale")

    assert cells[10:12] == ["100,00", "10,00%"]


@pytest.mark.parametrize("title, kind", TABLES)
def test_the_total_profit_sums_only_the_rows_that_show_one(client_logged, title, kind):
    a = SavingTypeFactory(title="A", type=kind)
    b = SavingTypeFactory(title="B", type=kind)
    buy(a, 100000)
    worth(a, 110000)
    buy(b, 50000)
    sell(b, 10000)

    cells = total_cells(_table(client_logged, title))

    assert cells[5] == "1.500,00"
    assert cells[-2:] == ["100,00", "10,00%"]


def test_a_switch_out_of_a_stale_fund_leaves_the_base_of_the_fund_that_shows(
    client_logged,
):
    a = SavingTypeFactory(title="A")
    b = SavingTypeFactory(title="B")
    buy(a, 100000)
    worth(a, 130000, month=3, day=1)
    SavingChangeFactory(
        from_account=a, to_account=b, price=130000, fee=0, date=date(YEAR, 6, 1)
    )
    worth(b, 140000)

    cells = total_cells(_table(client_logged))

    assert cells[5] == "2.300,00"
    assert cells[-2:] == ["100,00", "7,69%"]


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_funds_tab_queries_do_not_grow_with_stale_funds(client_logged, main_user, kind):
    queries = [
        view_queries(
            client_logged,
            main_user,
            "bookkeeping:tab_funds",
            lambda i: stale_fund(f"Fund {i}", kind),
            n,
        )
        for n in (2, 4)
    ]

    assert queries[0] == queries[1]
