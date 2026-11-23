import pytest

from ....savings.tests.factories import SavingTypeFactory
from ....users.models import User
from ..helper import (
    KINDS,
    funds_table,
    quiet_build,
    row_cells,
    stale_fund,
    switch_a_into_b,
    total_cells,
)
from ..signals.helpers import YEAR, buy, sell, worth

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("title, kind", KINDS)
def test_a_stale_worth_shows_dashes_in_the_profit_cells(
    client_logged, main_user, title, kind
):
    with quiet_build(main_user):
        stale_fund(kind=kind)

    cells = row_cells(funds_table(client_logged, title), "Stale")

    assert cells[9] == "1.000,00"
    assert cells[10:12] == ["-", "-"]


def test_a_stale_worth_shows_dashes_the_next_year_too(client_logged, main_user):
    with quiet_build(main_user):
        stale_fund()
    User.objects.update(year=YEAR + 1)

    cells = row_cells(funds_table(client_logged), "Stale")

    assert cells[10:12] == ["-", "-"]


def test_a_worth_dated_after_the_sell_shows_the_profit(client_logged, main_user):
    with quiet_build(main_user):
        fund = stale_fund()
        worth(fund, 70000)

    cells = row_cells(funds_table(client_logged), "Stale")

    assert cells[10:12] == ["100,00", "10,00%"]


@pytest.mark.parametrize("title, kind", KINDS)
def test_the_total_profit_sums_only_the_rows_that_show_one(
    client_logged, main_user, title, kind
):
    with quiet_build(main_user):
        a = SavingTypeFactory(title="A", type=kind)
        b = SavingTypeFactory(title="B", type=kind)
        buy(a, 100000)
        worth(a, 110000)
        buy(b, 50000)
        sell(b, 10000)

    cells = total_cells(funds_table(client_logged, title))

    assert cells[5] == "1.500,00"
    assert cells[-2:] == ["100,00", "10,00%"]


def test_a_switch_out_of_a_stale_fund_leaves_the_base_of_the_fund_that_shows(
    client_logged, main_user
):
    with quiet_build(main_user):
        switch_a_into_b()

    cells = total_cells(funds_table(client_logged))

    assert cells[5] == "2.300,00"
    assert cells[-2:] == ["100,00", "7,69%"]
