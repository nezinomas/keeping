from datetime import date as dt

import factory
import pytest
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save

from ....accounts.services.model_services import AccountBalanceModelService
from ....accounts.tests.factories import AccountBalance, AccountFactory
from ....incomes.tests.factories import IncomeFactory
from ....journals.tests.factories import JournalFactory
from ...models import Debt
from ...services.model_services import DebtModelService
from ..factories import BorrowFactory, LendFactory
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, assert_balance

pytestmark = pytest.mark.django_db


def test_debt_str():
    v = LendFactory.build(name="X")

    assert str(v) == "X"


def test_debt_returned_is_never_null():
    with pytest.raises(IntegrityError), transaction.atomic():
        LendFactory(returned=None)


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_related(main_user, second_user, debt_type):
    o = DEBT_FACTORIES[debt_type]()
    DEBT_FACTORIES[debt_type](
        journal=second_user.journal,
        account=AccountFactory(journal=second_user.journal, title="a2"),
    )

    actual = DebtModelService(main_user, debt_type).objects

    assert len(actual) == 1
    assert str(actual[0]) == str(o)


@factory.django.mute_signals(post_save)
def test_debt_related_queries(main_user, django_assert_num_queries):
    LendFactory()
    LendFactory()

    with django_assert_num_queries(1):
        list(x.account.title for x in list(DebtModelService(main_user, "lend").objects))


@factory.django.mute_signals(post_save)
def test_debt_sort(main_user):
    o1 = LendFactory(date=dt(1999, 1, 2))
    o2 = LendFactory(date=dt(1999, 12, 13))

    actual = DebtModelService(main_user, "lend").objects

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


@factory.django.mute_signals(post_save)
def test_debt_items(main_user, second_user):
    o1 = LendFactory()
    o2 = LendFactory(closed=True)
    LendFactory(name="X1", journal=second_user.journal)

    actual = DebtModelService(main_user, "lend").items()

    assert actual.count() == 2
    assert str(actual[0]) == str(o1)
    assert str(actual[1]) == str(o2)


@factory.django.mute_signals(post_save)
def test_debt_open_items(main_user, second_user):
    o1 = LendFactory(closed=False)
    LendFactory(closed=True)

    LendFactory(closed=False, journal=second_user.journal)

    actual = DebtModelService(main_user, "lend").open_items()

    assert actual.count() == 1
    assert actual[0].pk == o1.pk


@factory.django.mute_signals(post_save)
def test_debt_year(main_user):
    o = LendFactory(name="N1", date=dt(1999, 2, 3))
    LendFactory(name="N2", date=dt(2999, 2, 3), price=2)

    actual = DebtModelService(main_user, "lend").year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == str(o)
    assert actual[0].name == o.name
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == 100


@factory.django.mute_signals(post_save)
def test_debt_year_and_not_closed(main_user):
    o1 = LendFactory(date=dt(1974, 1, 1), closed=False)
    LendFactory(date=dt(1974, 12, 1), closed=True)
    o2 = LendFactory(date=dt(1999, 1, 1), closed=False)
    o3 = LendFactory(date=dt(1999, 12, 1), closed=True)

    actual = DebtModelService(main_user, "lend").year(1999)

    assert actual.count() == 3

    assert actual[0].date == o3.date
    assert actual[1].date == o2.date
    assert actual[2].date == o1.date


@pytest.mark.parametrize(
    "debt_type, incomes, expenses, balance",
    [
        pytest.param("lend", 0.0, 100.0, -100.0, id="lend"),
        pytest.param("borrow", 100.0, 0.0, 100.0, id="borrow"),
    ],
)
def test_debt_post_save_new(main_user, debt_type, incomes, expenses, balance):
    DEBT_FACTORIES[debt_type]()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert_balance(actual[0], incomes=incomes, expenses=expenses, balance=balance)


@pytest.mark.parametrize(
    "debt_type, before, after",
    [
        pytest.param(
            "lend",
            {"incomes": 0.0, "expenses": 1.0, "balance": -1.0},
            {"incomes": 0.0, "expenses": 2.0, "balance": -2.0},
            id="lend",
        ),
        pytest.param(
            "borrow",
            {"incomes": 1.0, "expenses": 0.0, "balance": 1.0},
            {"incomes": 2.0, "expenses": 0.0, "balance": 2.0},
            id="borrow",
        ),
    ],
)
def test_debt_post_save_update(debt_type, before, after):
    obj = DEBT_FACTORIES[debt_type](price=1)

    assert_balance(AccountBalance.objects.first(), **before)

    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.price = 2
    obj_update.save()

    assert_balance(AccountBalance.objects.first(), **after)


@pytest.mark.parametrize(
    "debt_type, incomes, expenses, balance",
    [
        pytest.param("lend", 0.0, 1.0, 4.0, id="lend"),
        pytest.param("borrow", 1.0, 0.0, 6.0, id="borrow"),
    ],
)
def test_debt_post_save_first_record(main_user, debt_type, incomes, expenses, balance):
    a = AccountFactory()
    j = JournalFactory()

    IncomeFactory(date=dt(1998, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    Debt.objects.create(
        date=dt(1999, 1, 1), price=1, account=a, journal=j, debt_type=debt_type
    )

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.past == 5.0
    assert_balance(actual, incomes=incomes, expenses=expenses, balance=balance)


@pytest.mark.parametrize(
    "debt_type, incomes, expenses, balance",
    [
        pytest.param("lend", 0.0, 5.0, -5.0, id="lend"),
        pytest.param("borrow", 5.0, 0.0, 5.0, id="borrow"),
    ],
)
def test_debt_post_save_update_with_nothing_changed(
    main_user, debt_type, incomes, expenses, balance
):
    obj = DEBT_FACTORIES[debt_type](price=5)

    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert_balance(actual[0], incomes=incomes, expenses=expenses, balance=balance)


@pytest.mark.parametrize(
    "debt_type, incomes, expenses, balance",
    [
        pytest.param("lend", 0.0, 5.0, -5.0, id="lend"),
        pytest.param("borrow", 5.0, 0.0, 5.0, id="borrow"),
    ],
)
def test_debt_post_save_change_account(debt_type, incomes, expenses, balance):
    account_old = AccountFactory()
    account_new = AccountFactory(title="XXX")

    obj = DEBT_FACTORIES[debt_type](price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    assert_balance(actual, incomes=incomes, expenses=expenses, balance=balance)

    obj_new = Debt.objects.get(pk=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    with pytest.raises(AccountBalance.DoesNotExist):
        AccountBalance.objects.get(account_id=account_old.pk, year=1999)

    actual = AccountBalance.objects.get(account_id=account_new.pk, year=1999)
    assert_balance(
        actual, incomes=incomes, expenses=expenses, balance=balance, title="XXX"
    )


@pytest.mark.parametrize(
    "debt_type, incomes, expenses, balance",
    [
        pytest.param("lend", 0.0, 10.0, -10.0, id="lend"),
        pytest.param("borrow", 10.0, 0.0, 10.0, id="borrow"),
    ],
)
def test_debt_post_delete(debt_type, incomes, expenses, balance):
    obj = DEBT_FACTORIES[debt_type](price=10)

    actual = AccountBalance.objects.first()
    assert_balance(actual, incomes=incomes, expenses=expenses, balance=balance)

    Debt.objects.get(pk=obj.pk).delete()

    assert not AccountBalance.objects.exists()


@pytest.mark.parametrize(
    "debt_type, before, after",
    [
        pytest.param(
            "lend",
            {"incomes": 0.0, "expenses": 11.0, "balance": -11.0},
            {"incomes": 0.0, "expenses": 1.0, "balance": -1.0},
            id="lend",
        ),
        pytest.param(
            "borrow",
            {"incomes": 11.0, "expenses": 0.0, "balance": 11.0},
            {"incomes": 1.0, "expenses": 0.0, "balance": 1.0},
            id="borrow",
        ),
    ],
)
def test_debt_post_delete_with_updt(debt_type, before, after):
    obj = DEBT_FACTORIES[debt_type](price=1)
    obj_delete = DEBT_FACTORIES[debt_type](price=10)

    assert AccountBalance.objects.count() == 2
    assert Debt.objects.count() == 2

    actual = AccountBalance.objects.get(account_id=obj.account_id, year=1999)
    assert_balance(actual, **before)

    Debt.objects.get(pk=obj_delete.pk).delete()

    actual = AccountBalance.objects.get(account_id=obj.account_id, year=1999)
    assert_balance(actual, **after)


def test_debt_unique_users(second_user):
    LendFactory(name="T1")
    LendFactory(
        name="T1",
        journal=second_user.journal,
        account=AccountFactory(journal=second_user.journal, title="a2"),
    )

    assert Debt.objects.filter(name="T1").count() == 2


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "closed, extra, expect",
    [
        pytest.param(
            False,
            {"date": dt(1999, 1, 1), "closed": True},
            [
                {"date": dt(1999, 1, 1), "sum_debt": 3, "sum_return": 2},
                {"date": dt(1999, 2, 1), "sum_debt": 5, "sum_return": 2},
            ],
            id="open_only",
        ),
        pytest.param(
            True,
            {"date": dt(1999, 1, 1), "price": 2, "returned": 2, "closed": True},
            [
                {"date": dt(1999, 1, 1), "sum_debt": 5, "sum_return": 4},
                {"date": dt(1999, 2, 1), "sum_debt": 5, "sum_return": 2},
            ],
            id="with_closed",
        ),
    ],
)
def test_debt_sum_all_months(main_user, closed, extra, expect):
    LendFactory(date=dt(1999, 1, 1), price=1, returned=1)
    LendFactory(date=dt(1999, 1, 2), price=2, returned=1)
    LendFactory(date=dt(1999, 2, 1), price=4, returned=1)
    LendFactory(date=dt(1999, 2, 2), price=1, returned=1)
    LendFactory(**extra)
    LendFactory(date=dt(1974, 1, 1))

    actual = list(DebtModelService(main_user, "lend").sum_by_month(1999, closed=closed))

    assert actual == [row | {"title": "lend"} for row in expect]


@factory.django.mute_signals(post_save)
def test_debt_sum_all_months_ordering(main_user, second_user):
    LendFactory(date=dt(1999, 1, 1), price=1)
    LendFactory(date=dt(1999, 1, 2), price=2)
    LendFactory(date=dt(1999, 1, 2), price=2, journal=second_user.journal)
    LendFactory(date=dt(1999, 2, 1), price=4)
    LendFactory(date=dt(1999, 2, 2), price=1)
    LendFactory(date=dt(1999, 2, 2), price=6, journal=second_user.journal)

    actual = list(DebtModelService(main_user, "lend").sum_by_month(1999))

    assert actual[0]["date"] == dt(1999, 1, 1)
    assert actual[1]["date"] == dt(1999, 2, 1)


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "open_debts, expect",
    [
        pytest.param(
            [
                (dt(1999, 1, 1), 2, 1),
                (dt(1999, 1, 2), 2, 1),
                (dt(1974, 1, 2), 3, 2),
            ],
            {"debt": 7, "debt_return": 4},
            id="open_debts_summed",
        ),
        pytest.param([], {"debt": 0, "debt_return": 0}, id="none_open"),
    ],
)
def test_debt_sum_all_not_closed(main_user, open_debts, expect):
    LendFactory(date=dt(1999, 1, 1), price=12, closed=True)
    for date, price, returned in open_debts:
        LendFactory(date=date, price=price, returned=returned)

    actual = DebtModelService(main_user, "lend").sum_all()

    assert actual == expect


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "factory_, other, debt_type, sums, key",
    [
        pytest.param(
            BorrowFactory,
            LendFactory,
            "borrow",
            lambda s: s.incomes(),
            "incomes",
            id="incomes",
        ),
        pytest.param(
            LendFactory,
            BorrowFactory,
            "lend",
            lambda s: s.expenses(),
            "expenses",
            id="expenses",
        ),
    ],
)
def test_debt_yearly_sums_per_account(main_user, factory_, other, debt_type, sums, key):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    factory_(date=dt(1970, 1, 1), account=a1, price=1)
    factory_(date=dt(1970, 1, 1), account=a1, price=2)
    factory_(date=dt(1970, 1, 1), account=a2, price=3)
    factory_(date=dt(1970, 1, 1), account=a2, price=4)

    factory_(date=dt(1999, 1, 1), account=a1, price=10)
    factory_(date=dt(1999, 1, 1), account=a1, price=20)
    factory_(date=dt(1999, 1, 1), account=a2, price=30)
    factory_(date=dt(1999, 1, 1), account=a2, price=40)

    other()

    actual = sums(DebtModelService(main_user, debt_type))

    assert [(row["year"], row["category_id"], row[key]) for row in actual] == [
        (1970, 1, 3),
        (1970, 2, 7),
        (1999, 1, 30),
        (1999, 2, 70),
    ]
