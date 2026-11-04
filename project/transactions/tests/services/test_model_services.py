from datetime import date
from itertools import pairwise

import pytest

from ....core.tests.utils import count_queries
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ...models import SavingChange
from ...services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
)
from ..factories import SavingChangeFactory, SavingCloseFactory
from ..kinds import by_fund_move

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]

FUNDS = ["funds", "shares"]


def _switch(
    price,
    *,
    source="funds",
    target="funds",
    date_=date(1999, 6, 1),
    source_closed=None,
):
    n = SavingType.objects.count()
    change = SavingChangeFactory(
        price=price,
        date=date_,
        from_account=SavingTypeFactory(title=f"From {n}", type=source),
        to_account=SavingTypeFactory(title=f"To {n}", type=target),
    )
    if source_closed:
        change.from_account.closed = source_closed
        change.from_account.save()
    return change


def test_switched_within_no_switches(main_user):
    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 0


def test_switched_within_sums_up_to_the_year(main_user):
    _switch(100000)
    _switch(25000, date_=date(1998, 1, 1))
    _switch(7000, date_=date(2000, 1, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 125000


def test_switched_within_leaves_out_a_source_closed_before_the_year(main_user):
    _switch(100000, source_closed=1998)
    _switch(5000, source_closed=1999)

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 5000


def test_switched_within_leaves_out_a_target_closed_before_the_year(main_user):
    change = _switch(100000)
    change.to_account.closed = 1998
    change.to_account.save()

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 0


def test_switched_within_needs_both_funds_of_the_types(main_user):
    _switch(100000, source="funds", target="pensions")
    _switch(20000, source="pensions", target="funds")

    service = SavingChangeModelService(main_user)

    assert service.switched_within(1999, FUNDS) == 0
    assert service.switched_within(1999, ["pensions"]) == 0


def test_switched_within_pensions(main_user):
    _switch(100000, source="pensions", target="pensions")

    service = SavingChangeModelService(main_user)

    assert service.switched_within(1999, ["pensions"]) == 100000
    assert service.switched_within(1999, FUNDS) == 0


def test_switched_within_query_count_does_not_grow(main_user):
    def queries_with(switches):
        while SavingChange.objects.count() < switches:
            _switch(1000)
        return count_queries(
            lambda: SavingChangeModelService(main_user).switched_within(1999, FUNDS)
        )

    assert queries_with(2) == queries_with(6)


def _fund(title, closed=None):
    return SavingTypeFactory(title=title, type="funds", closed=closed)


def _move(source, target, price, date_=date(1998, 6, 1)):
    return SavingChangeFactory(
        price=price, date=date_, from_account=source, to_account=target
    )


def _closed_fund():
    return _fund("B", closed=1998), frozenset()


def _hidden_fund():
    fund = _fund("B")
    return fund, frozenset({fund.pk})


@pytest.mark.parametrize(
    "off_table, paid_in",
    [
        pytest.param(_closed_fund, 50000, id="closed"),
        pytest.param(_closed_fund, 30000, id="closed_with_its_gain"),
        pytest.param(_hidden_fund, 50000, id="hidden"),
    ],
)
def test_switched_within_follows_a_chain_through_a_fund_off_the_table(
    main_user, off_table, paid_in
):
    a = _fund("A")
    b, hidden = off_table()
    c = _fund("C")
    _move(a, b, paid_in)
    _move(b, c, 50000, date(1998, 7, 1))

    actual = SavingChangeModelService(main_user).switched_within(
        1999, FUNDS, hidden=hidden
    )

    assert actual == 50000


def test_switched_within_follows_a_two_deep_chain(main_user):
    a, d = _fund("A"), _fund("D")
    b, c = _fund("B", closed=1997), _fund("C", closed=1998)
    _move(a, b, 50000, date(1997, 1, 1))
    _move(b, c, 50000, date(1997, 6, 1))
    _move(c, d, 50000, date(1998, 6, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


def test_switched_within_passes_on_all_a_closed_fund_holds(main_user):
    a, b = _fund("A"), _fund("B", closed=1998)
    c, d = _fund("C"), _fund("D")
    _move(a, b, 50000)
    _move(b, c, 30000, date(1998, 7, 1))
    _move(b, d, 30000, date(1998, 8, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 60000


def test_switched_within_same_day_does_not_hang_on_entry_order(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(b, c, 50000, date(1998, 6, 1))
    _move(a, b, 50000, date(1998, 6, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


def _buy(fund, price, date_=date(1998, 6, 1)):
    return SavingFactory(saving_type=fund, price=price, fee=0, date=date_)


@pytest.mark.parametrize(
    "off_table",
    [
        pytest.param(_closed_fund, id="closed"),
        pytest.param(_hidden_fund, id="hidden"),
    ],
)
def test_switched_within_takes_the_table_share_of_a_fund_off_the_table(
    main_user, off_table
):
    a = _fund("A")
    b, hidden = off_table()
    c = _fund("C")
    _buy(b, 20000)
    _move(a, b, 40000)
    _move(b, c, 70000, date(1998, 7, 1))

    actual = SavingChangeModelService(main_user).switched_within(
        1999, FUNDS, hidden=hidden
    )

    assert actual == 46667


def test_switched_within_leaves_out_a_purchase_after_the_switch(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(a, b, 40000)
    _move(b, c, 50000, date(1998, 7, 1))
    _buy(b, 20000, date(1998, 8, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


def test_switched_within_counts_a_purchase_on_the_switch_day(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(a, b, 40000)
    _buy(b, 40000, date(1998, 7, 1))
    _move(b, c, 80000, date(1998, 7, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 40000


def test_switched_within_ignores_a_zero_price_purchase(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(a, b, 40000)
    SavingFactory(saving_type=b, price=0, fee=0, date=date(1998, 6, 1))
    _move(b, c, 50000, date(1998, 7, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


def test_switched_within_starts_over_in_a_fund_emptied_and_filled_again(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(a, b, 40000)
    _move(b, c, 40000, date(1998, 7, 1))
    _buy(b, 40000, date(1998, 8, 1))
    _move(b, c, 40000, date(1998, 9, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 40000


def test_switched_within_starts_over_after_outside_money_left(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _buy(b, 40000)
    _move(b, c, 40000, date(1998, 7, 1))
    _move(a, b, 40000, date(1998, 8, 1))
    _move(b, c, 40000, date(1998, 9, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 40000


def test_switched_within_reads_money_from_another_type_as_outside(main_user):
    a, b, c = _fund("A"), _fund("B"), _fund("C")
    shares = SavingTypeFactory(title="S", type="shares")
    _move(a, b, 10000)
    _move(shares, b, 10000)
    _move(b, c, 20000, date(1998, 7, 1))

    actual = SavingChangeModelService(main_user).switched_within(
        1999, ["funds"], hidden=frozenset({b.pk})
    )

    assert actual == 10000


@pytest.mark.parametrize("depth", [1, 2], ids=["one_fund", "two_funds"])
def test_switched_within_follows_money_through_funds_of_another_type(main_user, depth):
    pensions = [SavingTypeFactory(title=f"P{i}", type="pensions") for i in range(depth)]
    chain = [_fund("X"), *pensions, _fund("Y")]
    for day, (source, target) in enumerate(pairwise(chain), start=1):
        _move(source, target, 100000, date(1998, 1, day))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 100000


def test_switched_within_through_a_closed_fund_query_count_does_not_grow(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")

    def queries_with(rows):
        while SavingChange.objects.count() < rows:
            _buy(b, 1000)
            _move(a, b, 1000)
            _move(b, c, 1000, date(1998, 7, 1))
        return count_queries(
            lambda: SavingChangeModelService(main_user).switched_within(1999, FUNDS)
        )

    assert queries_with(2) == queries_with(6)


@by_fund_move
def test_moves_are_one_row_per_move_out(main_user, kind):
    fund = SavingTypeFactory(title="Fund")
    for day, price in ((1, 100), (1, 200), (2, 300)):
        kind.factory(from_account=fund, price=price, fee=10, date=date(1999, 6, day))

    actual = sorted(kind.service(main_user).moves(), key=lambda x: x["price"])

    assert actual == [
        {"category_id": fund.pk, "date": date(1999, 6, 1), "price": 100},
        {"category_id": fund.pk, "date": date(1999, 6, 1), "price": 200},
        {"category_id": fund.pk, "date": date(1999, 6, 2), "price": 300},
    ]


def test_moves_query_count_does_not_grow(main_user):
    def queries():
        return count_queries(
            lambda: (
                list(SavingChangeModelService(main_user).moves()),
                list(SavingCloseModelService(main_user).moves()),
            )
        )

    def add(rows):
        for _ in range(rows):
            SavingChangeFactory(price=1, fee=0, date=date(1999, 6, 1))
            SavingCloseFactory(price=1, fee=0, date=date(1999, 6, 1))

    add(2)
    few = queries()
    add(4)
    many = queries()

    assert many == few


@pytest.mark.parametrize(
    "hidden_of, switched",
    [
        pytest.param(lambda a, b: {"hidden": frozenset({a.pk})}, 0, id="source"),
        pytest.param(lambda a, b: {"hidden": frozenset({b.pk})}, 0, id="target"),
        pytest.param(lambda a, b: {}, 130000, id="defaults_to_no_fund"),
    ],
)
def test_switched_within_leaves_out_only_the_hidden_funds(
    main_user, hidden_of, switched
):
    a, b = _fund("A"), _fund("B")
    _move(a, b, 130000)

    actual = SavingChangeModelService(main_user).switched_within(
        1999, FUNDS, **hidden_of(a, b)
    )

    assert actual == switched


def _years_scene():
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _buy(b, 20000)
    _move(a, b, 40000)
    _move(b, c, 70000, date(1998, 7, 1))
    _move(a, c, 10000, date(1999, 3, 1))
    return a, b, c


def test_switched_within_years_reads_each_year(main_user):
    _years_scene()
    service = SavingChangeModelService(main_user)

    actual = service.switched_within_years([1998, 1999], FUNDS)

    assert actual == {1998: 110000, 1999: 56667}


def test_switched_within_years_hides_funds_per_year(main_user):
    _, _, c = _years_scene()
    service = SavingChangeModelService(main_user)

    actual = service.switched_within_years(
        [1998, 1999], FUNDS, hidden_by_year={1999: frozenset({c.pk})}
    )

    assert actual == {1998: 110000, 1999: 0}


def test_switched_within_years_query_count_does_not_grow_with_the_years(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1990), _fund("C")

    def queries_with(years):
        while SavingChange.objects.count() < 2 * years:
            year = 1990 + SavingChange.objects.count() // 2
            _buy(b, 1000, date(year, 1, 1))
            _move(a, b, 1000, date(year, 2, 1))
            _move(b, c, 1000, date(year, 3, 1))
        return count_queries(
            lambda: SavingChangeModelService(main_user).switched_within_years(
                list(range(1990, 1990 + years)), FUNDS
            )
        )

    assert queries_with(2) == queries_with(6)
