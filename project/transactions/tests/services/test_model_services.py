from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....savings.models import SavingType
from ....savings.tests.factories import SavingTypeFactory
from ...models import SavingChange
from ...services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)
from ..factories import SavingChangeFactory, SavingCloseFactory

FUNDS = ["funds", "shares"]


def test_transaction_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        TransactionModelService(user=None)


def test_transaction_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        TransactionModelService(user=anon)


@pytest.mark.django_db
def test_transaction_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    TransactionModelService(user=main_user)


def test_saving_close_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingCloseModelService(user=None)


def test_saving_close_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingCloseModelService(user=anon)


@pytest.mark.django_db
def test_saving_close_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingCloseModelService(user=main_user)


def test_saving_change_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingChangeModelService(user=None)


def test_saving_change_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingChangeModelService(user=anon)


@pytest.mark.django_db
def test_saving_change_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingChangeModelService(user=main_user)


def _switch(
    price,
    *,
    source="funds",
    target="funds",
    date_=date(1999, 6, 1),
    source_closed=None,
):
    n = SavingType.objects.count()
    return SavingChangeFactory(
        price=price,
        date=date_,
        from_account=SavingTypeFactory(
            title=f"From {n}", type=source, closed=source_closed
        ),
        to_account=SavingTypeFactory(title=f"To {n}", type=target),
    )


@pytest.mark.django_db
def test_switched_within_no_switches(main_user):
    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 0


@pytest.mark.django_db
def test_switched_within_sums_up_to_the_year(main_user):
    _switch(100000)
    _switch(25000, date_=date(1998, 1, 1))
    _switch(7000, date_=date(2000, 1, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 125000


@pytest.mark.django_db
def test_switched_within_leaves_out_a_source_closed_before_the_year(main_user):
    _switch(100000, source_closed=1998)
    _switch(5000, source_closed=1999)

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 5000


@pytest.mark.django_db
def test_switched_within_leaves_out_a_target_closed_before_the_year(main_user):
    change = _switch(100000)
    change.to_account.closed = 1998
    change.to_account.save()

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 0


@pytest.mark.django_db
def test_switched_within_needs_both_funds_of_the_types(main_user):
    _switch(100000, source="funds", target="pensions")
    _switch(20000, source="pensions", target="funds")

    service = SavingChangeModelService(main_user)

    assert service.switched_within(1999, FUNDS) == 0
    assert service.switched_within(1999, ["pensions"]) == 0


@pytest.mark.django_db
def test_switched_within_pensions(main_user):
    _switch(100000, source="pensions", target="pensions")

    service = SavingChangeModelService(main_user)

    assert service.switched_within(1999, ["pensions"]) == 100000
    assert service.switched_within(1999, FUNDS) == 0


@pytest.mark.django_db
def test_switched_within_query_count_does_not_grow(main_user):
    def queries_with(switches):
        while SavingChange.objects.count() < switches:
            _switch(1000)
        with CaptureQueriesContext(connection) as ctx:
            SavingChangeModelService(main_user).switched_within(1999, FUNDS)
        return len(ctx)

    assert queries_with(2) == queries_with(6) == 1


def _fund(title, closed=None):
    return SavingTypeFactory(title=title, type="funds", closed=closed)


def _move(source, target, price, date_=date(1998, 6, 1)):
    return SavingChangeFactory(
        price=price, date=date_, from_account=source, to_account=target
    )


@pytest.mark.django_db
def test_switched_within_follows_a_chain_through_a_closed_fund(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(a, b, 50000)
    _move(b, c, 50000, date(1998, 7, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


@pytest.mark.django_db
def test_switched_within_caps_at_what_the_closed_fund_received(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(a, b, 30000)
    _move(b, c, 50000, date(1998, 7, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 30000


@pytest.mark.django_db
def test_switched_within_follows_a_two_deep_chain(main_user):
    a, d = _fund("A"), _fund("D")
    b, c = _fund("B", closed=1997), _fund("C", closed=1998)
    _move(a, b, 50000, date(1997, 1, 1))
    _move(b, c, 50000, date(1997, 6, 1))
    _move(c, d, 50000, date(1998, 6, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


@pytest.mark.django_db
def test_switched_within_counts_a_closed_funds_money_once(main_user):
    a, b = _fund("A"), _fund("B", closed=1998)
    c, d = _fund("C"), _fund("D")
    _move(a, b, 50000)
    _move(b, c, 30000, date(1998, 7, 1))
    _move(b, d, 30000, date(1998, 8, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


@pytest.mark.django_db
def test_switched_within_same_day_does_not_hang_on_entry_order(main_user):
    a, b, c = _fund("A"), _fund("B", closed=1998), _fund("C")
    _move(b, c, 50000, date(1998, 6, 1))
    _move(a, b, 50000, date(1998, 6, 1))

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 50000


# ----------------------------------------------------------------------------
#                                                           moves out of a fund
# ----------------------------------------------------------------------------
@pytest.mark.django_db
def test_saving_change_moves_one_row_per_move_out(main_user):
    fund = SavingTypeFactory(title="Fund")
    other = SavingTypeFactory(title="Other")
    for day, price in ((1, 100), (1, 200), (2, 300)):
        SavingChangeFactory(
            from_account=fund,
            to_account=other,
            price=price,
            fee=0,
            date=date(1999, 6, day),
        )

    actual = sorted(
        SavingChangeModelService(main_user).moves(), key=lambda x: x["price"]
    )

    assert actual == [
        {"category_id": fund.pk, "date": date(1999, 6, 1), "price": 100},
        {"category_id": fund.pk, "date": date(1999, 6, 1), "price": 200},
        {"category_id": fund.pk, "date": date(1999, 6, 2), "price": 300},
    ]


@pytest.mark.django_db
def test_saving_close_moves_one_row_per_move_out(main_user):
    fund = SavingTypeFactory(title="Fund")
    SavingCloseFactory(from_account=fund, price=500, fee=10, date=date(1999, 6, 1))

    actual = list(SavingCloseModelService(main_user).moves())

    assert actual == [{"category_id": fund.pk, "date": date(1999, 6, 1), "price": 500}]


@pytest.mark.django_db
def test_moves_query_count_does_not_grow(main_user):
    def queries():
        with CaptureQueriesContext(connection) as context:
            list(SavingChangeModelService(main_user).moves())
            list(SavingCloseModelService(main_user).moves())
        return len(context)

    for _ in range(2):
        SavingChangeFactory(price=1, fee=0, date=date(1999, 6, 1))
    few = queries()
    for _ in range(4):
        SavingChangeFactory(price=1, fee=0, date=date(1999, 6, 1))
    many = queries()

    assert many == few


# ----------------------------------------------------------------------------
#                                          funds whose row shows no profit
# ----------------------------------------------------------------------------
@pytest.mark.django_db
def test_switched_within_leaves_out_a_hidden_source(main_user):
    a, b = _fund("A"), _fund("B")
    _move(a, b, 130000)

    actual = SavingChangeModelService(main_user).switched_within(
        1999, FUNDS, hidden=frozenset({a.pk})
    )

    assert actual == 0


@pytest.mark.django_db
def test_switched_within_leaves_out_a_hidden_target(main_user):
    a, b = _fund("A"), _fund("B")
    _move(a, b, 130000)

    actual = SavingChangeModelService(main_user).switched_within(
        1999, FUNDS, hidden=frozenset({b.pk})
    )

    assert actual == 0


@pytest.mark.django_db
def test_switched_within_follows_a_chain_through_a_hidden_fund(main_user):
    a, b, c = _fund("A"), _fund("B"), _fund("C")
    _move(a, b, 50000)
    _move(b, c, 50000, date(1998, 7, 1))

    actual = SavingChangeModelService(main_user).switched_within(
        1999, FUNDS, hidden=frozenset({b.pk})
    )

    assert actual == 50000


@pytest.mark.django_db
def test_switched_within_hidden_defaults_to_no_fund(main_user):
    a, b = _fund("A"), _fund("B")
    _move(a, b, 130000)

    assert SavingChangeModelService(main_user).switched_within(1999, FUNDS) == 130000
