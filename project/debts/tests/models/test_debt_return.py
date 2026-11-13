from datetime import date as dt

import factory
import pytest
from django.db.models.signals import post_save

from ....accounts.models import AccountBalance
from ....accounts.services.model_services import AccountBalanceModelService
from ....accounts.tests.factories import AccountFactory
from ....incomes.tests.factories import IncomeFactory
from ...models import Debt, DebtReturn
from ...services.model_services import DebtReturnModelService
from ..factories import BorrowReturnFactory
from ..helpers import (
    DEBT_FACTORIES,
    DEBT_TYPES,
    RETURN_FACTORIES,
    assert_balance,
)

pytestmark = pytest.mark.django_db

LEND_BEFORE = {"incomes": 6, "expenses": 100, "balance": -94}
BORROW_BEFORE = {"incomes": 100, "expenses": 5, "balance": 95}


@pytest.mark.parametrize(
    "debt_type, expected",
    [
        pytest.param(Debt.DebtType.LEND, "Grąžino 0.06", id="lend"),
        pytest.param(Debt.DebtType.BORROW, "Grąžinau 0.05", id="borrow"),
    ],
)
def test_debt_return_str(debt_type, expected):
    v = RETURN_FACTORIES[debt_type].build()

    assert str(v) == expected


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "debt_type, expected",
    [
        pytest.param(Debt.DebtType.LEND, "Grąžino 0.01", id="lend"),
        pytest.param(Debt.DebtType.BORROW, "Grąžinau 0.01", id="borrow"),
    ],
)
def test_debt_return_related(main_user, second_user, debt_type, expected):
    b1 = DEBT_FACTORIES[debt_type](name="B1", price=1)
    b2 = DEBT_FACTORIES[debt_type](name="B2", price=2, journal=second_user.journal)

    RETURN_FACTORIES[debt_type](debt=b1, price=1.1)
    RETURN_FACTORIES[debt_type](debt=b2, price=2.1)

    actual = DebtReturnModelService(main_user, debt_type).objects.get()

    assert str(actual) == expected


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_items(main_user, debt_type):
    RETURN_FACTORIES[debt_type]()
    RETURN_FACTORIES[debt_type]()

    actual = DebtReturnModelService(main_user, debt_type).items()

    assert actual.count() == 2


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_year(main_user, debt_type):
    RETURN_FACTORIES[debt_type]()
    RETURN_FACTORIES[debt_type](date=dt(1974, 1, 2))

    actual = DebtReturnModelService(main_user, debt_type).year(1999)

    assert actual.count() == 1


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "debt_type, title",
    [
        pytest.param(Debt.DebtType.LEND, "lend_return", id="lend"),
        pytest.param(Debt.DebtType.BORROW, "borrow_return", id="borrow"),
    ],
)
def test_debt_return_sum_by_month(main_user, debt_type, title):
    return_factory = RETURN_FACTORIES[debt_type]
    return_factory()
    return_factory(date=dt(1974, 3, 2), price=1)
    return_factory(date=dt(1974, 3, 3), price=2)
    return_factory(date=dt(1974, 3, 4), price=3)

    actual = DebtReturnModelService(main_user, debt_type).sum_by_month(1974)

    expect = {"date": dt(1974, 3, 1), "title": title, "sum": 6}
    assert list(actual) == [expect]


@pytest.mark.parametrize(
    "returned, prices, expect",
    [
        pytest.param(50, (10,), 10, id="replaces_a_stale_value"),
        pytest.param(0, (10, 11), 21, id="two_returns"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@pytest.mark.usefixtures("quiet_syncs")
def test_debt_return_post_save_debt_return_value(
    main_user, debt_type, returned, prices, expect
):
    debt2 = DEBT_FACTORIES[debt_type](name="Z")
    debt1 = DEBT_FACTORIES[debt_type](name="A", returned=returned)

    for price in prices:
        RETURN_FACTORIES[debt_type](debt=debt1, price=price)
    RETURN_FACTORIES[debt_type](debt=debt2, price=20)

    assert Debt.objects.get(pk=debt1.pk).returned == expect


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@pytest.mark.usefixtures("quiet_syncs")
def test_debt_return_moved_to_another_debt_updates_both(main_user, debt_type):
    debt1 = DEBT_FACTORIES[debt_type](name="A")
    debt2 = DEBT_FACTORIES[debt_type](name="Z")
    debt_return = RETURN_FACTORIES[debt_type](debt=debt1, price=30)

    debt_return.debt = debt2
    debt_return.save()

    assert Debt.objects.get(pk=debt1.pk).returned == 0
    assert Debt.objects.get(pk=debt2.pk).returned == 30


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@pytest.mark.usefixtures("quiet_syncs")
def test_debt_return_post_delete_debt_return_value(main_user, debt_type):
    debt1 = DEBT_FACTORIES[debt_type](name="A")
    debt2 = DEBT_FACTORIES[debt_type](name="Z")

    debt_return = RETURN_FACTORIES[debt_type](debt=debt1, price=10)
    RETURN_FACTORIES[debt_type](debt=debt2, price=20)

    debt_return.delete()

    assert Debt.objects.get(pk=debt1.pk).returned == 0
    assert Debt.objects.get(pk=debt2.pk).returned == 20


def _price_set_to_one(obj):
    obj.price = 1
    obj.save()


@pytest.mark.parametrize(
    "debt_type, change, kept_prices, before, after",
    [
        pytest.param(
            Debt.DebtType.LEND,
            _price_set_to_one,
            (),
            LEND_BEFORE,
            {"incomes": 1, "expenses": 100, "balance": -99},
            id="lend_updated",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            _price_set_to_one,
            (),
            BORROW_BEFORE,
            {"incomes": 100, "expenses": 1, "balance": 99},
            id="borrow_updated",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            DebtReturn.delete,
            (),
            LEND_BEFORE,
            {"incomes": 0, "expenses": 100, "balance": -100},
            id="lend_deleted",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            DebtReturn.delete,
            (1,),
            {"incomes": 7, "expenses": 100, "balance": -93},
            {"incomes": 1, "expenses": 100, "balance": -99},
            id="lend_deleted_beside_another",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            DebtReturn.delete,
            (),
            BORROW_BEFORE,
            {"incomes": 100, "expenses": 0, "balance": 100},
            id="borrow_deleted",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            DebtReturn.delete,
            (1,),
            {"incomes": 100, "expenses": 6, "balance": 94},
            {"incomes": 100, "expenses": 1, "balance": 99},
            id="borrow_deleted_beside_another",
        ),
    ],
)
def test_debt_return_post_save_or_delete(debt_type, change, kept_prices, before, after):
    obj = RETURN_FACTORIES[debt_type]()
    for price in kept_prices:
        RETURN_FACTORIES[debt_type](debt=obj.debt, price=price)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert_balance(actual, **before)

    change(DebtReturn.objects.get(pk=obj.pk))

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert_balance(actual, **after)


@pytest.mark.parametrize(
    "debt_type, incomes, expenses, balance, delta",
    [
        pytest.param(Debt.DebtType.LEND, 2, 5, -2, 2, id="lend"),
        pytest.param(Debt.DebtType.BORROW, 5, 2, 4, -4, id="borrow"),
    ],
)
def test_debt_return_post_save_first_record(
    main_user, debt_type, incomes, expenses, balance, delta
):
    obj = DEBT_FACTORIES[debt_type](price=5)

    IncomeFactory(date=dt(1998, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    RETURN_FACTORIES[debt_type](date=dt(1999, 1, 1), debt=obj, price=2)

    actual = AccountBalanceModelService(main_user).items()

    rows = [
        (row.year, row.past, row.incomes, row.expenses, row.balance, row.delta)
        for row in actual
    ]
    assert rows == [
        (1998, 0, 1, 0, 1, -1),
        (1999, 1, incomes, expenses, balance, delta),
        # the sync writes a next-year row carrying the balance forward
        (2000, balance, 0, 0, balance, delta),
    ]


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "prices, expect",
    [
        pytest.param([1, 2], 3, id="its_returns_summed"),
        pytest.param([], 0, id="no_returns"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_total_returned_for_debt(main_user, debt_type, prices, expect):
    debt = DEBT_FACTORIES[debt_type](name="A")
    RETURN_FACTORIES[debt_type](debt=DEBT_FACTORIES[debt_type](name="Z"), price=5)
    for price in prices:
        RETURN_FACTORIES[debt_type](debt=debt, price=price)

    service = DebtReturnModelService(main_user, debt_type)
    actual = service.total_returned_for_debt(debt)

    assert actual == expect


def test_debt_return_journal_is_its_accounts(second_user):
    journal = second_user.journal

    obj = BorrowReturnFactory.build(account=AccountFactory(journal=journal))

    assert obj.journal == journal
