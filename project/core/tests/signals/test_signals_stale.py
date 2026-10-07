from datetime import date

import pytest

from ....bookkeeping import balance_sources
from ....bookkeeping.tests.factories import PensionWorthFactory
from ....pensions.models import PensionBalance
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingBalance
from ....savings.tests.factories import SavingTypeFactory
from ..utils import count_queries
from .helpers import (
    YEAR,
    balance,
    buy,
    sell,
    switch_out,
    worth,
    worth_date,
)

pytestmark = pytest.mark.django_db


MOVE_OUT = {
    "sell": lambda fund, price, when: sell(fund, price, when=when),
    "switch": switch_out,
}


def _stale_fund(move_out):
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    worth(fund, 100000, month=3, day=1)
    MOVE_OUT[move_out](fund, 40000, date(YEAR, 6, 1))
    return fund


@pytest.mark.parametrize("move_out", MOVE_OUT)
def test_a_worth_older_than_a_move_out_is_stale(move_out):
    fund = _stale_fund(move_out)

    actual = balance(fund)
    assert actual.sold_since_check == 40000
    assert actual.shows_profit is False


@pytest.mark.parametrize("move_out", MOVE_OUT)
def test_a_stale_worth_stays_stale_in_the_next_year(move_out):
    fund = _stale_fund(move_out)

    actual = balance(fund, YEAR + 1)
    assert actual.sold_since_check == 40000
    assert actual.shows_profit is False


def test_a_worth_dated_after_the_move_out_clears_it():
    fund = _stale_fund("sell")
    worth(fund, 60000)

    actual = balance(fund)
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True


def test_a_move_out_on_the_worths_own_day_is_stale():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    worth(fund, 100000, month=6, day=1)
    sell(fund, 40000, when=date(YEAR, 6, 1))

    actual = balance(fund)
    assert actual.sold_since_check == 40000
    assert actual.shows_profit is False


def test_a_move_out_before_the_worth_is_not_stale():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    sell(fund, 40000, when=date(YEAR, 3, 1))
    worth(fund, 60000, month=6, day=1)

    assert balance(fund).sold_since_check == 0


def test_a_move_out_of_a_later_year_is_not_stale_for_the_earlier_row():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    worth(fund, 100000, month=3, day=1)
    sell(fund, 40000, when=date(YEAR + 1, 6, 1))

    assert balance(fund, YEAR).sold_since_check == 0
    assert balance(fund, YEAR + 1).sold_since_check == 40000


def test_moves_since_the_check_add_up_across_years():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    worth(fund, 100000, month=3, day=1)
    sell(fund, 10000, when=date(YEAR, 6, 1))
    sell(fund, 5000, when=date(YEAR + 1, 6, 1))

    assert balance(fund, YEAR).sold_since_check == 10000
    assert balance(fund, YEAR + 1).sold_since_check == 15000


def test_the_close_year_rule_keeps_precedence_over_staleness():
    fund = SavingTypeFactory(title="Fund", closed=YEAR)
    buy(fund, 100000)
    worth(fund, 100000, month=3, day=1)
    sell(fund, 40000)

    actual = balance(fund)
    assert actual.market_value == 0
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True


def test_a_fund_with_no_worth_is_not_stale_and_shows_no_profit():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    sell(fund, 40000)

    actual = balance(fund)
    assert actual.sold_since_check == 0
    assert actual.shows_profit is False


def test_a_fund_with_no_moves_out_is_not_stale():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    worth(fund, 120000)

    actual = balance(fund)
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True


def test_a_pension_is_never_stale():
    pension = PensionTypeFactory(title="Pension")
    PensionFactory(pension_type=pension, price=100000, fee=0, date=date(YEAR, 1, 1))
    PensionWorthFactory(pension_type=pension, price=120000, date=worth_date())

    actual = PensionBalance.objects.get(pension_type=pension, year=YEAR)
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True


def _funds_with_moves(first, count):
    for i in range(first, first + count):
        fund = SavingTypeFactory(title=f"M{i}")
        buy(fund, 100000)
        worth(fund, 100000, month=3, day=1)
        sell(fund, 1000, when=date(YEAR, 6, 1))
        switch_out(fund, 1000, date(YEAR, 7, 1))


def test_resync_query_count_with_moves_does_not_grow_with_the_funds(main_user):
    def queries():
        SavingBalance.objects.all().delete()
        return count_queries(lambda: balance_sources.sync_savings(user=main_user))

    _funds_with_moves(0, 2)
    few = queries()
    _funds_with_moves(2, 4)
    many = queries()

    assert many == few
