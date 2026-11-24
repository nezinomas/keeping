from datetime import date

import pytest

from ....bookkeeping.tests.helper import quiet_build
from ....savings.tests.factories import SavingTypeFactory
from .helpers import (
    YEAR,
    balance,
    buy,
    sell,
    switch_out,
    worth,
)

pytestmark = pytest.mark.django_db


MOVE_OUT = {
    "sell": lambda fund, price, when: sell(fund, price, when=when),
    "switch": switch_out,
}


def _stale_fund(move_out, user):
    with quiet_build(user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        worth(fund, 100000, month=3, day=1)
    MOVE_OUT[move_out](fund, 40000, date(YEAR, 6, 1))
    return fund


def _sell_on_the_worths_day(user):
    with quiet_build(user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        worth(fund, 100000, month=6, day=1)
    sell(fund, 40000, when=date(YEAR, 6, 1))
    return fund


def _worth_after_the_sell(user):
    fund = _stale_fund("sell", user)
    worth(fund, 60000)
    return fund


def _sell_before_the_worth(user):
    with quiet_build(user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        sell(fund, 40000, when=date(YEAR, 3, 1))
    worth(fund, 60000, month=6, day=1)
    return fund


def _sell_without_a_worth(user):
    with quiet_build(user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
    sell(fund, 40000)
    return fund


@pytest.mark.parametrize(
    "arrange, year, expected",
    [
        *(
            pytest.param(
                lambda user, move=move: _stale_fund(move, user),
                year,
                (40000, False),
                id=f"{move}{when}",
            )
            for move in ("sell", "switch")
            for year, when in ((YEAR, ""), (YEAR + 1, "-in-the-next-year"))
        ),
        pytest.param(_sell_on_the_worths_day, YEAR, (40000, False), id="own-day"),
        pytest.param(_worth_after_the_sell, YEAR, (0, True), id="worth-after-the-sell"),
        pytest.param(_sell_before_the_worth, YEAR, (0, True), id="sell-before-worth"),
        pytest.param(_sell_without_a_worth, YEAR, (0, False), id="no-worth"),
    ],
)
def test_a_worth_shows_the_profit_unless_a_move_out_is_dated_on_or_after_it(
    main_user, arrange, year, expected
):
    fund = arrange(main_user)

    actual = balance(fund, year)
    assert (actual.sold_since_check, actual.shows_profit) == expected


def test_a_move_out_of_a_later_year_is_not_stale_for_the_earlier_row(main_user):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        worth(fund, 100000, month=3, day=1)
    sell(fund, 40000, when=date(YEAR + 1, 6, 1))

    assert balance(fund, YEAR).sold_since_check == 0
    assert balance(fund, YEAR + 1).sold_since_check == 40000


def test_moves_since_the_check_add_up_across_years(main_user):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        worth(fund, 100000, month=3, day=1)
        sell(fund, 10000, when=date(YEAR, 6, 1))
    sell(fund, 5000, when=date(YEAR + 1, 6, 1))

    assert balance(fund, YEAR).sold_since_check == 10000
    assert balance(fund, YEAR + 1).sold_since_check == 15000


def test_the_close_year_rule_keeps_precedence_over_staleness(main_user):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund", closed=YEAR)
        buy(fund, 100000)
        worth(fund, 100000, month=3, day=1)
    sell(fund, 40000)

    actual = balance(fund)
    assert actual.market_value == 0
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True


@pytest.mark.parametrize("closed", [None, YEAR], ids=["open", "closed"])
def test_a_fund_with_no_moves_out_keeps_its_worth_and_is_not_stale(closed):
    fund = SavingTypeFactory(title="Fund", closed=closed)
    buy(fund, 100000)
    worth(fund, 120000)

    actual = balance(fund)
    assert actual.market_value == 120000
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True
    assert actual.profit_sum == 20000
    assert actual.profit_proc == 20.0
