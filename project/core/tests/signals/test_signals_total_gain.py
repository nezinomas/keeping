from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....accounts.tests.factories import AccountFactory
from ....bookkeeping.tests.factories import PensionWorthFactory, SavingWorthFactory
from ....pensions.models import PensionBalance
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingBalance, SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory, SavingCloseFactory
from ...services import signals_service

pytestmark = pytest.mark.django_db

TZ = ZoneInfo("Europe/Vilnius")
YEAR = 1999


def _worth_date(month=12, day=31, year=YEAR):
    return datetime(year, month, day, 12, tzinfo=TZ)


def _balance(saving_type, year=YEAR):
    return SavingBalance.objects.get(saving_type=saving_type, year=year)


def _buy(saving_type, price, fee=0, when=date(YEAR, 1, 1)):
    return SavingFactory(saving_type=saving_type, price=price, fee=fee, date=when)


def _sell(saving_type, price, fee=0, when=date(YEAR, 6, 1)):
    return SavingCloseFactory(
        from_account=saving_type,
        to_account=AccountFactory(title="Bank"),
        price=price,
        fee=fee,
        date=when,
    )


def _worth(saving_type, price, month=12, day=31, year=YEAR):
    return SavingWorthFactory(
        saving_type=saving_type, price=price, date=_worth_date(month, day, year)
    )


# ----------------------------------------------------------------------------
#                                          total gain: market value + taken out
# ----------------------------------------------------------------------------
def test_partial_sell_counts_the_money_taken_out():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 100000)
    _worth(fund, 120000, month=3, day=1)
    _sell(fund, 60000)
    _worth(fund, 60000)

    actual = _balance(fund)
    assert actual.sold == 60000
    assert actual.market_value == 60000
    assert actual.profit_sum == 20000
    assert actual.profit_proc == 20.0


def test_full_close_counts_the_money_taken_out_net_of_its_fee():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 100000, fee=1000)
    _sell(fund, 95000, fee=5000)
    _worth(fund, 0)

    actual = _balance(fund)
    assert actual.profit_sum == -6000
    assert actual.profit_proc == -6.0


def test_switch_moves_the_gain_to_the_fund_it_left():
    a = SavingTypeFactory(title="A")
    b = SavingTypeFactory(title="B")
    _buy(a, 100000)
    _worth(a, 130000, month=3, day=1)
    SavingChangeFactory(
        from_account=a, to_account=b, price=130000, fee=0, date=date(YEAR, 6, 1)
    )
    _worth(b, 140000)
    _worth(a, 0)

    gain_a = _balance(a).profit_sum
    gain_b = _balance(b).profit_sum
    assert gain_a == 30000
    assert gain_b == 10000
    assert gain_a + gain_b == 140000 - 100000


# ----------------------------------------------------------------------------
#                                                                    close year
# ----------------------------------------------------------------------------
def test_closed_fund_with_a_sell_reads_no_market_value_in_its_close_year():
    fund = SavingTypeFactory(title="SEB", closed=YEAR)
    _buy(fund, 200000, fee=7000, when=date(YEAR, 1, 1))
    _buy(fund, 217700, fee=7988, when=date(YEAR, 2, 1))
    _sell(fund, 372728, fee=68675, when=date(YEAR, 11, 5))
    _worth(fund, 441403)

    actual = _balance(fund)
    assert actual.incomes == 417700
    assert actual.fee == 14988
    assert (actual.sold, actual.sold_fee) == (372728, 68675)
    assert actual.market_value == 0
    assert actual.profit_sum == -59960
    assert actual.profit_proc == -14.35


def test_fund_closed_without_a_sell_keeps_its_worth():
    fund = SavingTypeFactory(title="Fund", closed=YEAR)
    _buy(fund, 100000)
    _worth(fund, 120000)

    actual = _balance(fund)
    assert actual.market_value == 120000
    assert actual.profit_sum == 20000
    assert actual.profit_proc == 20.0


def test_closed_pension_keeps_its_worth():
    pension = PensionTypeFactory(title="Pension", closed=YEAR)
    PensionFactory(pension_type=pension, price=100000, fee=0, date=date(YEAR, 1, 1))
    PensionWorthFactory(pension_type=pension, price=120000, date=_worth_date())

    actual = PensionBalance.objects.get(pension_type=pension, year=YEAR)
    assert actual.market_value == 120000
    assert actual.profit_sum == 20000
    assert actual.profit_proc == 20.0


def test_open_partly_sold_fund_without_a_worth_reads_what_was_taken_out():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 100000, fee=1000)
    _sell(fund, 40000)

    actual = _balance(fund)
    assert actual.market_value == 0
    assert actual.profit_sum == -61000
    assert actual.profit_proc == -61.0


# ----------------------------------------------------------------------------
#                                                      closing a type re-syncs
# ----------------------------------------------------------------------------
def test_closing_the_type_after_the_sell_zeroes_the_worth():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 100000, fee=1000)
    _sell(fund, 110000)
    _worth(fund, 110000)

    fund.closed = YEAR
    fund.save()

    actual = _balance(fund)
    assert actual.market_value == 0
    assert actual.profit_sum == 110000 - 100000 - 1000


def _sold_last_year_by_a_sell(fund):
    _buy(fund, 100000, when=date(YEAR - 1, 1, 1))
    _sell(fund, 110000, when=date(YEAR - 1, 6, 1))


def _sold_last_year_by_a_switch(fund):
    _buy(fund, 100000, when=date(YEAR - 1, 1, 1))
    SavingChangeFactory(
        from_account=fund,
        to_account=SavingTypeFactory(title="Other"),
        price=110000,
        fee=0,
        date=date(YEAR - 1, 6, 1),
    )


@pytest.mark.parametrize(
    "take_out",
    [_sold_last_year_by_a_sell, _sold_last_year_by_a_switch],
    ids=lambda take_out: take_out.__name__.removeprefix("_sold_last_year_by_a_"),
)
def test_fund_sold_last_year_reads_no_worth_in_its_close_year(take_out):
    fund = SavingTypeFactory(title="Fund", closed=YEAR)
    take_out(fund)
    _worth(fund, 110000)

    actual = _balance(fund)
    assert actual.market_value == 0
    assert actual.profit_sum == 10000


def test_closing_a_pension_type_drops_its_later_rows():
    pension = PensionTypeFactory(title="Pension")
    for year in (YEAR, YEAR + 1):
        PensionFactory(pension_type=pension, price=10000, fee=0, date=date(year, 1, 1))
        PensionWorthFactory(
            pension_type=pension, price=11000, date=_worth_date(year=year)
        )
    assert PensionBalance.objects.filter(pension_type=pension, year=YEAR + 1).exists()

    pension.closed = YEAR
    pension.save()

    years = PensionBalance.objects.filter(pension_type=pension).values_list(
        "year", flat=True
    )
    assert max(years) == YEAR


# ----------------------------------------------------------------------------
#                                 deleting a move re-derives the fund's close year
# ----------------------------------------------------------------------------
def _switch(saving_type, price, when):
    return SavingChangeFactory(
        from_account=saving_type,
        to_account=SavingTypeFactory(title="Other"),
        price=price,
        fee=0,
        date=when,
    )


MOVE_OUT = {
    "sell": lambda fund, when: _sell(fund, 10000, when=when),
    "switch": lambda fund, when: _switch(fund, 10000, when),
}


def _closed(fund):
    return SavingType.objects.get(pk=fund.pk).closed


@pytest.mark.parametrize("move", MOVE_OUT)
def test_deleting_the_closing_move_closes_the_fund_at_the_move_before(move):
    fund = SavingTypeFactory(title="Fund", closed=YEAR + 1)
    _buy(fund, 100000)
    MOVE_OUT[move](fund, date(YEAR, 6, 1))
    closing = MOVE_OUT[move](fund, date(YEAR + 1, 6, 1))

    closing.delete()

    assert _closed(fund) == YEAR


@pytest.mark.parametrize("move", MOVE_OUT)
def test_deleting_the_only_move_reopens_the_fund(move):
    fund = SavingTypeFactory(title="Fund", closed=YEAR)
    _buy(fund, 100000)
    closing = MOVE_OUT[move](fund, date(YEAR, 6, 1))

    closing.delete()

    assert _closed(fund) is None


@pytest.mark.parametrize("move", MOVE_OUT)
def test_deleting_a_move_leaves_an_open_fund_open(move):
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 100000)
    MOVE_OUT[move](fund, date(YEAR, 6, 1))
    later = MOVE_OUT[move](fund, date(YEAR + 1, 6, 1))

    later.delete()

    assert _closed(fund) is None


# ----------------------------------------------------------------------------
#                                        a row with nothing taken out is as before
# ----------------------------------------------------------------------------
def _no_worth():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 10000)
    return fund, {YEAR: (-10000, 0.0)}


def _worth_below_cost():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 10000, fee=100)
    _worth(fund, 9000)
    return fund, {YEAR: (-1100, -11.0)}


def _fee_only_without_worth():
    fund = SavingTypeFactory(title="Fund")
    SavingFactory(saving_type=fund, price=0, fee=100, date=date(YEAR, 1, 1))
    return fund, {YEAR: (-100, 0.0)}


def _fee_only_with_worth():
    fund = SavingTypeFactory(title="Fund")
    SavingFactory(saving_type=fund, price=0, fee=100, date=date(YEAR, 1, 1))
    _worth(fund, 500)
    return fund, {YEAR: (400, 0.0)}


def _several_years():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 10000, fee=100, when=date(1998, 1, 1))
    _buy(fund, 5000, fee=50)
    _worth(fund, 16000)
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
        actual = _balance(fund, year)
        assert actual.sold == 0
        assert (actual.profit_sum, actual.profit_proc) == (profit_sum, profit_proc)


def test_pension_reads_as_before():
    pension = PensionTypeFactory(title="Pension")
    PensionFactory(pension_type=pension, price=10000, fee=100, date=date(YEAR, 1, 1))
    PensionWorthFactory(pension_type=pension, price=11000, date=_worth_date())

    actual = PensionBalance.objects.get(pension_type=pension, year=YEAR)
    assert actual.profit_sum == 900
    assert actual.profit_proc == 9.0


def test_new_fund_before_its_first_worth_reads_no_percent():
    fund = SavingTypeFactory(title="Fund")
    _buy(fund, 10000, fee=100, when=date(1998, 1, 1))
    _worth(fund, 12000)

    actual = _balance(fund, 1998)
    assert actual.market_value == 0
    assert actual.profit_proc == 0.0


# ----------------------------------------------------------------------------
#                                                                   query count
# ----------------------------------------------------------------------------
def _fund_with_worth(title):
    fund = SavingTypeFactory(title=title)
    _buy(fund, 100000, fee=10)
    _worth(fund, 90000)
    return fund


def _close_with_a_sell_after_a_switch_in(closed, other):
    closed.closed = YEAR
    closed.save()
    _sell(closed, 50000)
    SavingChangeFactory(
        from_account=other,
        to_account=closed,
        price=1000,
        fee=0,
        date=date(YEAR, 5, 1),
    )


def _resync_queries(main_user):
    SavingBalance.objects.all().delete()
    with CaptureQueriesContext(connection) as context:
        signals_service.sync_savings(instance=None, user=main_user)
    assert SavingBalance.objects.exists()
    return len(context)


def _save_queries(type_):
    with CaptureQueriesContext(connection) as context:
        type_.save()
    return len(context)


def test_saving_a_saving_type_query_count_does_not_grow_with_the_types():
    funds = [_fund_with_worth(f"T{i}") for i in range(2)]
    few = _save_queries(funds[0])

    funds += [_fund_with_worth(f"T{i}") for i in range(2, 6)]
    many = _save_queries(funds[0])

    assert many == few


def _pension_with_worth(title):
    pension = PensionTypeFactory(title=title)
    PensionFactory(pension_type=pension, price=10000, fee=0, date=date(YEAR, 1, 1))
    PensionWorthFactory(pension_type=pension, price=11000, date=_worth_date())
    return pension


def test_saving_a_pension_type_query_count_does_not_grow_with_the_types():
    pensions = [_pension_with_worth(f"P{i}") for i in range(2)]
    few = _save_queries(pensions[0])

    pensions += [_pension_with_worth(f"P{i}") for i in range(2, 6)]
    many = _save_queries(pensions[0])

    assert many == few


def test_resync_query_count_does_not_grow_with_the_types(main_user):
    funds = [_fund_with_worth(f"T{i}") for i in range(2)]
    _close_with_a_sell_after_a_switch_in(*funds)
    few = _resync_queries(main_user)

    for i in range(2, 6):
        _fund_with_worth(f"T{i}")
    many = _resync_queries(main_user)

    assert many == few
