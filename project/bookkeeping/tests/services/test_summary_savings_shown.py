from datetime import date

import pytest

from ....core.tests.utils import count_queries
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ...services import savings, summary_savings
from ..factories import PensionWorthFactory
from ..signals.helpers import (
    YEAR,
    buy,
    sell,
    worth,
    worth_date,
)

pytestmark = pytest.mark.django_db


def _chart(user, pointer="funds"):
    return summary_savings.load(user)["charts"][pointer]


def _figures(chart, year=YEAR):
    i = chart["categories"].index(year)
    return {
        "total": chart["total"][i],
        "profit": chart["profit"][i],
        "invested": chart["invested"][i],
        "proc": chart["proc"][i],
    }


def test_a_year_without_a_sell_or_switch_reads_as_it_did(main_user):
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    worth(fund, 120000)

    assert _figures(_chart(main_user)) == {
        "total": 120000,
        "profit": 20000,
        "invested": 100000,
        "proc": 20.0,
    }


def test_the_viso_holds_what_is_left_after_a_sell(main_user):
    fund = SavingTypeFactory(title="Fund")
    buy(fund, 100000)
    sell(fund, 40000)
    worth(fund, 70000)

    assert _figures(_chart(main_user)) == {
        "total": 70000,
        "profit": 10000,
        "invested": 60000,
        "proc": 10.0,
    }


def test_a_stale_worth_stays_out_of_all_three_figures(main_user):
    stale = SavingTypeFactory(title="Stale")
    buy(stale, 100000)
    worth(stale, 100000, month=3, day=1)
    sell(stale, 40000)
    fresh = SavingTypeFactory(title="Fresh")
    buy(fresh, 50000)
    worth(fresh, 60000)

    assert _figures(_chart(main_user)) == {
        "total": 60000,
        "profit": 10000,
        "invested": 50000,
        "proc": 20.0,
    }


def _switch_scene():
    a, b = SavingTypeFactory(title="A"), SavingTypeFactory(title="B")
    buy(a, 100000)
    SavingChangeFactory(
        from_account=a, to_account=b, price=40000, fee=0, date=date(YEAR, 6, 1)
    )
    worth(a, 70000)
    worth(b, 45000)


def test_a_year_with_a_switch_reads_the_funds_table_percent(main_user):
    _switch_scene()

    table = savings.load_service(main_user, YEAR)["total_row"]["profit_proc"]
    chart = _figures(_chart(main_user))

    assert chart["proc"] == round(table, 1) == 15.0


def test_the_funds_and_shares_chart_takes_the_same_switch_off(main_user):
    _switch_scene()

    assert _figures(_chart(main_user, "funds_shares"))["proc"] == 15.0


def test_pensions_ii_counts_only_the_rows_that_show_a_profit(main_user):
    shown, hidden = PensionTypeFactory(title="Shown"), PensionTypeFactory(title="Hid")
    PensionFactory(pension_type=shown, price=10000, fee=0)
    PensionFactory(pension_type=hidden, price=5000, fee=0)
    PensionWorthFactory(
        pension_type=shown,
        price=12000,
        date=worth_date(),
    )

    assert _figures(_chart(main_user, "pensions2")) == {
        "total": 12000,
        "profit": 2000,
        "invested": 10000,
        "proc": 20.0,
    }


def _grow(years):
    """Adds the funds of each of the last `years` years not yet there."""
    for k in range(years):
        year = date.today().year - k
        if SavingType.objects.filter(title=f"A{year}").exists():
            continue
        a = SavingTypeFactory(title=f"A{year}")
        closed = SavingTypeFactory(title=f"C{year}", closed=year)
        c = SavingTypeFactory(title=f"T{year}")
        stale = SavingTypeFactory(title=f"S{year}")
        buy(a, 100000, when=date(year, 1, 1))
        buy(closed, 20000, when=date(year, 1, 1))
        SavingChangeFactory(
            from_account=a, to_account=closed, price=40000, date=date(year, 2, 1)
        )
        SavingChangeFactory(
            from_account=closed, to_account=c, price=70000, date=date(year, 3, 1)
        )
        worth(a, 70000, year=year)
        worth(c, 80000, year=year)
        buy(stale, 1000, when=date(year, 1, 1))
        worth(stale, 1000, month=3, day=1, year=year)
        sell(stale, 100, when=date(year, 6, 1))


def _queries(user, years):
    _grow(years)
    return count_queries(lambda: _chart(user))


def test_the_chart_queries_do_not_grow_with_the_years(main_user):
    two = _queries(main_user, 2)
    six = _queries(main_user, 6)

    assert two == six


def test_money_from_another_type_is_outside_the_funds_chart(main_user):
    a, b, c = (SavingTypeFactory(title=t, type="funds") for t in "ABC")
    shares = SavingTypeFactory(title="S", type="shares")
    buy(a, 30000)
    buy(shares, 10000)
    for source, target, price, month in [
        (a, b, 10000, 6),
        (shares, b, 10000, 6),
        (b, c, 20000, 7),
    ]:
        SavingChangeFactory(
            from_account=source,
            to_account=target,
            price=price,
            fee=0,
            date=date(YEAR, month, 1),
        )
    worth(a, 20000)
    worth(c, 22000)

    assert _figures(_chart(main_user))["proc"] == 5.0
    assert _figures(_chart(main_user, "funds_shares"))["proc"] == 5.0
