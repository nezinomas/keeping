from datetime import date

import pytest

from ....bookkeeping.tests.factories import PensionWorthFactory
from ....bookkeeping.tests.helper import quiet_build, switch_after_a_gain
from ....core.tests.utils import count_queries
from ....pensions.models import PensionBalance
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.tests.factories import SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from .helpers import (
    YEAR,
    balance,
    buy,
    resync_queries,
    sell,
    switch_out,
    worth,
    worth_date,
)

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                          total gain: market value + taken out
# ----------------------------------------------------------------------------
def test_partial_sell_counts_the_money_taken_out(main_user):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000)
        worth(fund, 120000, month=3, day=1)
        sell(fund, 60000)
    worth(fund, 60000)

    actual = balance(fund)
    assert actual.sold == 60000
    assert actual.market_value == 60000
    assert actual.profit_sum == 20000
    assert actual.profit_proc == 20.0


def test_full_close_counts_the_money_taken_out_net_of_its_fee(main_user):
    with quiet_build(main_user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000, fee=1000)
        sell(fund, 95000, fee=5000)
    worth(fund, 0)

    actual = balance(fund)
    assert actual.profit_sum == -6000
    assert actual.profit_proc == -6.0


def test_switch_moves_the_gain_to_the_fund_it_left(main_user):
    with quiet_build(main_user):
        a, b = switch_after_a_gain()
    worth(a, 0)

    gain_a = balance(a).profit_sum
    gain_b = balance(b).profit_sum
    assert gain_a == 30000
    assert gain_b == 10000
    assert gain_a + gain_b == 140000 - 100000


# ----------------------------------------------------------------------------
#                                                                    close year
# ----------------------------------------------------------------------------
def _sold_in_its_close_year(user):
    with quiet_build(user):
        fund = SavingTypeFactory(title="SEB", closed=YEAR)
        buy(fund, 200000, fee=7000, when=date(YEAR, 1, 1))
        buy(fund, 217700, fee=7988, when=date(YEAR, 2, 1))
        sell(fund, 372728, fee=68675, when=date(YEAR, 11, 5))
    worth(fund, 441403)
    return fund


def _closed_after_the_sell(user):
    with quiet_build(user):
        fund = SavingTypeFactory(title="Fund")
        buy(fund, 100000, fee=1000)
        sell(fund, 110000)
        worth(fund, 110000)

    fund.closed = YEAR
    fund.save()
    return fund


def _sold_last_year_by_a_sell(fund):
    buy(fund, 100000, when=date(YEAR - 1, 1, 1))
    sell(fund, 110000, when=date(YEAR - 1, 6, 1))


def _sold_last_year_by_a_switch(fund):
    buy(fund, 100000, when=date(YEAR - 1, 1, 1))
    SavingChangeFactory(
        from_account=fund,
        to_account=SavingTypeFactory(title="Other"),
        price=110000,
        fee=0,
        date=date(YEAR - 1, 6, 1),
    )


def _closed_with_the_worth_after_being_sold_last_year(user, take_out):
    with quiet_build(user):
        fund = SavingTypeFactory(title="Fund")
        take_out(fund)
        fund.closed = YEAR
        fund.save()
    worth(fund, 110000)
    return fund


@pytest.mark.parametrize(
    "arrange, expected",
    [
        pytest.param(
            _sold_in_its_close_year,
            (417700, 14988, 372728, 68675, 0, -59960, -14.35),
            id="sell-in-the-close-year",
        ),
        pytest.param(
            _closed_after_the_sell,
            (100000, 1000, 110000, 0, 0, 9000, 9.0),
            id="closed-after-the-sell",
        ),
        pytest.param(
            lambda user: _closed_with_the_worth_after_being_sold_last_year(
                user, _sold_last_year_by_a_sell
            ),
            (100000, 0, 110000, 0, 0, 10000, 10.0),
            id="sold-last-year-by-a-sell",
        ),
        pytest.param(
            lambda user: _closed_with_the_worth_after_being_sold_last_year(
                user, _sold_last_year_by_a_switch
            ),
            (100000, 0, 110000, 0, 0, 10000, 10.0),
            id="sold-last-year-by-a-switch",
        ),
    ],
)
def test_a_closed_fund_that_was_sold_reads_no_market_value_in_its_close_year(
    main_user, arrange, expected
):
    fund = arrange(main_user)

    actual = balance(fund)
    assert (
        actual.incomes,
        actual.fee,
        actual.sold,
        actual.sold_fee,
        actual.market_value,
        actual.profit_sum,
        actual.profit_proc,
    ) == expected


def test_open_partly_sold_fund_without_a_worth_reads_what_was_taken_out():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000, fee=1000)
    sell(fund, 40000)

    actual = balance(fund)
    assert actual.market_value == 0
    assert actual.profit_sum == -61000
    assert actual.profit_proc == -61.0


# ----------------------------------------------------------------------------
#                                                      closing a type re-syncs
# ----------------------------------------------------------------------------
def test_closing_a_pension_type_drops_its_later_rows(main_user):
    with quiet_build(main_user):
        pension = PensionTypeFactory(title="Pension")
        for year in (YEAR, YEAR + 1):
            PensionFactory(
                pension_type=pension, price=10000, fee=0, date=date(year, 1, 1)
            )
            PensionWorthFactory(
                pension_type=pension, price=11000, date=worth_date(year=year)
            )
    assert PensionBalance.objects.filter(pension_type=pension, year=YEAR + 1).exists()

    pension.closed = YEAR
    pension.save()

    years = PensionBalance.objects.filter(pension_type=pension).values_list(
        "year", flat=True
    )
    assert max(years) == YEAR


# ----------------------------------------------------------------------------
#                                        a row with nothing taken out is as before
# ----------------------------------------------------------------------------
def _no_worth():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 10000)
    return fund, {YEAR: (-10000, 0.0)}


def _worth_below_cost():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 10000, fee=100)
    worth(fund, 9000)
    return fund, {YEAR: (-1100, -11.0)}


def _fee_only_without_worth():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 0, fee=100)
    return fund, {YEAR: (-100, 0.0)}


def _fee_only_with_worth():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 0, fee=100)
    worth(fund, 500)
    return fund, {YEAR: (400, 0.0)}


def _several_years():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 10000, fee=100, when=date(1998, 1, 1))
    buy(fund, 5000, fee=50)
    worth(fund, 16000)
    return fund, {1998: (-10100, 0.0), 1999: (850, 5.67), 2000: (850, 5.67)}


@pytest.mark.parametrize(
    "build",
    [
        _no_worth,
        _worth_below_cost,
        _fee_only_without_worth,
        _fee_only_with_worth,
        _several_years,
    ],
    ids=lambda build: build.__name__.lstrip("_"),
)
def test_row_with_nothing_taken_out_reads_as_before(build):
    fund, expected = build()

    for year, (profit_sum, profit_proc) in expected.items():
        actual = balance(fund, year)
        assert actual.sold == 0
        assert (actual.profit_sum, actual.profit_proc) == (profit_sum, profit_proc)


@pytest.mark.parametrize(
    "closed, price, fee, worth_price, expected",
    [
        pytest.param(YEAR, 100000, 0, 120000, (120000, 20000, 20.0), id="closed"),
        pytest.param(None, 10000, 100, 11000, (11000, 900, 9.0), id="open"),
        pytest.param(None, 100000, 0, 120000, (120000, 20000, 20.0), id="open-no-fee"),
    ],
)
def test_pension_keeps_its_worth_and_is_never_stale_open_or_closed(
    closed, price, fee, worth_price, expected
):
    pension = PensionTypeFactory(title="Pension", closed=closed)
    PensionFactory(pension_type=pension, price=price, fee=fee, date=date(YEAR, 1, 1))
    PensionWorthFactory(pension_type=pension, price=worth_price, date=worth_date())

    actual = PensionBalance.objects.get(pension_type=pension, year=YEAR)
    assert (actual.market_value, actual.profit_sum, actual.profit_proc) == expected
    assert actual.sold_since_check == 0
    assert actual.shows_profit is True


def test_new_fund_before_its_first_worth_reads_no_percent():
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 10000, fee=100, when=date(1998, 1, 1))
    worth(fund, 12000)

    actual = balance(fund, 1998)
    assert actual.market_value == 0
    assert actual.profit_proc == 0.0


# ----------------------------------------------------------------------------
#                                                                   query count
# ----------------------------------------------------------------------------
def _fund_with_worth(title):
    fund = SavingTypeFactory(title=title)
    buy(fund, 100000, fee=10)
    worth(fund, 90000)
    return fund


def _close_with_a_sell_after_a_switch_in(closed, other):
    closed.closed = YEAR
    closed.save()
    sell(closed, 50000)
    SavingChangeFactory(
        from_account=other,
        to_account=closed,
        price=1000,
        fee=0,
        date=date(YEAR, 5, 1),
    )


def _two_funds_one_closed_by_a_sell_after_a_switch_in():
    _close_with_a_sell_after_a_switch_in(*[_fund_with_worth(f"T{i}") for i in range(2)])


def _two_more_funds():
    for i in range(2, 4):
        _fund_with_worth(f"T{i}")


def _funds_with_moves(first, count):
    for i in range(first, first + count):
        fund = SavingTypeFactory(title=f"M{i}")
        buy(fund, 100000)
        worth(fund, 100000, month=3, day=1)
        sell(fund, 1000, when=date(YEAR, 6, 1))
        switch_out(fund, 1000, date(YEAR, 7, 1))


def _save_queries(type_):
    return count_queries(type_.save)


def _pension_with_worth(title):
    pension = PensionTypeFactory(title=title)
    PensionFactory(pension_type=pension, price=10000, fee=0, date=date(YEAR, 1, 1))
    PensionWorthFactory(pension_type=pension, price=11000, date=worth_date())
    return pension


@pytest.mark.parametrize(
    "build",
    [_fund_with_worth, _pension_with_worth],
    ids=["saving_type", "pension_type"],
)
def test_saving_a_type_query_count_does_not_grow_with_the_types(main_user, build):
    with quiet_build(main_user):
        types = [build(f"T{i}") for i in range(2)]
    few = _save_queries(types[0])

    with quiet_build(main_user):
        types += [build(f"T{i}") for i in range(2, 6)]
    many = _save_queries(types[0])

    assert many == few


@pytest.mark.parametrize(
    "build_few, build_more",
    [
        pytest.param(
            _two_funds_one_closed_by_a_sell_after_a_switch_in,
            _two_more_funds,
            id="closed-by-a-sell-after-a-switch-in",
        ),
        pytest.param(
            lambda: _funds_with_moves(0, 2),
            lambda: _funds_with_moves(2, 2),
            id="moves-out",
        ),
    ],
)
def test_resync_query_count_does_not_grow_with_the_funds(
    main_user, build_few, build_more
):
    with quiet_build(main_user):
        build_few()
    few = resync_queries(main_user)

    with quiet_build(main_user):
        build_more()
    many = resync_queries(main_user)

    assert many == few
