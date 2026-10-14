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
from ..factories import BorrowReturnFactory, LendFactory, LendReturnFactory
from ..helpers import DEBT_FACTORIES, RETURN_FACTORIES, assert_balance

pytestmark = pytest.mark.django_db


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

    actual = DebtReturnModelService(main_user, debt_type).objects

    assert actual.count() == 1
    assert str(actual[0]) == expected


@factory.django.mute_signals(post_save)
def test_lend_return_related_queries(main_user, django_assert_num_queries):
    LendReturnFactory()
    LendReturnFactory()

    with django_assert_num_queries(1):
        list(
            x.account.title
            for x in list(DebtReturnModelService(main_user, Debt.DebtType.LEND).objects)
        )


@factory.django.mute_signals(post_save)
def test_lend_return_items(main_user):
    LendReturnFactory()
    LendReturnFactory()

    actual = DebtReturnModelService(main_user, Debt.DebtType.LEND).items()

    assert actual.count() == 2


@factory.django.mute_signals(post_save)
def test_lend_return_year(main_user):
    LendReturnFactory()
    LendReturnFactory(date=dt(1974, 1, 2))

    actual = DebtReturnModelService(main_user, Debt.DebtType.LEND).year(1999)

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
    "debt_type, expected",
    [
        pytest.param(
            Debt.DebtType.LEND,
            {"incomes": 6, "expenses": 100, "balance": -94},
            id="lend",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            {"incomes": 100, "expenses": 5, "balance": 95},
            id="borrow",
        ),
    ],
)
def test_debt_return_post_save_new(main_user, debt_type, expected):
    RETURN_FACTORIES[debt_type]()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert_balance(actual[0], **expected)


@pytest.mark.parametrize(
    "returned, prices, expect",
    [
        pytest.param(0, (10,), 10, id="one_return"),
        pytest.param(50, (10,), 10, id="replaces_a_stale_value"),
        pytest.param(0, (10, 11), 21, id="two_returns"),
    ],
)
def test_lend_return_post_save_debt_return_value(main_user, returned, prices, expect):
    debt2 = LendFactory(name="Z")
    debt1 = LendFactory(name="A", returned=returned)

    for price in prices:
        LendReturnFactory(debt=debt1, price=price)
    LendReturnFactory(debt=debt2, price=20)

    assert Debt.objects.get(pk=debt1.pk).returned == expect


def test_lend_return_moved_to_another_debt_updates_both(main_user):
    debt1 = LendFactory(name="A")
    debt2 = LendFactory(name="Z")
    debt_return = LendReturnFactory(debt=debt1, price=30)

    debt_return.debt = debt2
    debt_return.save()

    assert Debt.objects.get(pk=debt1.pk).returned == 0
    assert Debt.objects.get(pk=debt2.pk).returned == 30


def test_lend_return_post_delete_debt_return_value(main_user):
    debt1 = LendFactory(name="A")
    debt2 = LendFactory(name="Z")

    debt_return = LendReturnFactory(debt=debt1, price=10)
    LendReturnFactory(debt=debt2, price=20)

    actual = Debt.objects.get(pk=debt1.pk)
    assert actual.returned == 10

    debt_return.delete()

    actual = Debt.objects.get(pk=debt1.pk)
    assert actual.returned == 0


@pytest.mark.parametrize(
    "debt_type, before, after",
    [
        pytest.param(
            Debt.DebtType.LEND,
            {"incomes": 6, "expenses": 100, "balance": -94},
            {"incomes": 1, "expenses": 100, "balance": -99},
            id="lend",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            {"incomes": 100, "expenses": 5, "balance": 95},
            {"incomes": 100, "expenses": 1, "balance": 99},
            id="borrow",
        ),
    ],
)
def test_debt_return_post_save_update(debt_type, before, after):
    obj = RETURN_FACTORIES[debt_type]()

    assert_balance(AccountBalance.objects.first(), **before)

    obj_update = DebtReturn.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    assert_balance(AccountBalance.objects.first(), **after)


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

    assert actual[0].year == 1998
    assert actual[0].past == 0
    assert actual[0].incomes == 1
    assert actual[0].expenses == 0
    assert actual[0].balance == 1
    assert actual[0].delta == -1

    assert actual[1].year == 1999
    assert actual[1].past == 1
    assert actual[1].incomes == incomes
    assert actual[1].expenses == expenses
    assert actual[1].balance == balance
    assert actual[1].delta == delta


@pytest.mark.parametrize(
    "debt_type, before, after",
    [
        pytest.param(
            Debt.DebtType.LEND,
            {"incomes": 6, "expenses": 100, "balance": -94},
            {"incomes": 0, "expenses": 100, "balance": -100},
            id="lend",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            {"incomes": 100, "expenses": 5, "balance": 95},
            {"incomes": 100, "expenses": 0, "balance": 100},
            id="borrow",
        ),
    ],
)
def test_debt_return_post_delete(debt_type, before, after):
    obj = RETURN_FACTORIES[debt_type]()

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert_balance(actual, **before)

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert_balance(actual, **after)


@pytest.mark.parametrize(
    "debt_type, before, after",
    [
        pytest.param(
            Debt.DebtType.LEND,
            {"incomes": 3, "expenses": 100, "balance": -97},
            {"incomes": 1, "expenses": 100, "balance": -99},
            id="lend",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            {"incomes": 100, "expenses": 3, "balance": 97},
            {"incomes": 100, "expenses": 1, "balance": 99},
            id="borrow",
        ),
    ],
)
def test_debt_return_post_delete_with_updt(debt_type, before, after):
    return_factory = RETURN_FACTORIES[debt_type]
    b = DEBT_FACTORIES[debt_type]()
    return_factory(debt=b, price=1)

    obj = return_factory(debt=b, price=2)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert_balance(actual, **before)

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert_balance(actual, **after)


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "factory_, other, debt_type, sums, key",
    [
        pytest.param(
            LendReturnFactory,
            BorrowReturnFactory,
            Debt.DebtType.LEND,
            lambda s: s.incomes(),
            "incomes",
            id="incomes",
        ),
        pytest.param(
            BorrowReturnFactory,
            LendReturnFactory,
            Debt.DebtType.BORROW,
            lambda s: s.expenses(),
            "expenses",
            id="expenses",
        ),
    ],
)
def test_debt_return_yearly_sums_per_account(
    main_user, factory_, other, debt_type, sums, key
):
    a1 = AccountFactory(title="A1", order=20)
    a2 = AccountFactory(title="A2")

    factory_(date=dt(1970, 1, 1), account=a1, price=1)
    factory_(date=dt(1970, 1, 1), account=a1, price=2)
    factory_(date=dt(1970, 1, 1), account=a2, price=3)
    factory_(date=dt(1970, 1, 1), account=a2, price=4)

    factory_(date=dt(1999, 1, 1), account=a1, price=10)
    factory_(date=dt(1999, 1, 1), account=a1, price=20)
    factory_(date=dt(1999, 1, 1), account=a2, price=30)
    factory_(date=dt(1999, 1, 1), account=a2, price=40)

    other(date=dt(1999, 1, 1), account=a2, price=180)

    actual = sums(DebtReturnModelService(main_user, debt_type))

    assert [(row["year"], row["category_id"], row[key]) for row in actual] == [
        (1970, 1, 3),
        (1970, 2, 7),
        (1999, 1, 30),
        (1999, 2, 70),
    ]


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "prices, expect",
    [
        pytest.param([1, 2], 3, id="its_returns_summed"),
        pytest.param([], 0, id="no_returns"),
    ],
)
def test_debt_return_total_returned_for_debt(main_user, prices, expect):
    debt = LendFactory(name="A")
    LendReturnFactory(debt=LendFactory(name="Z"), price=5)
    for price in prices:
        LendReturnFactory(debt=debt, price=price)

    service = DebtReturnModelService(main_user, Debt.DebtType.LEND)
    actual = service.total_returned_for_debt(debt)

    assert actual == expect


def test_debt_return_journal_is_its_accounts(second_user):
    journal = second_user.journal

    obj = BorrowReturnFactory.build(account=AccountFactory(journal=journal))

    assert obj.journal == journal
