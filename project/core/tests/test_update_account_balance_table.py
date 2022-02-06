from datetime import date

import pytest

from ...accounts.factories import (AccountBalance, AccountBalanceFactory,
                                   AccountFactory)
from ...accounts.lib.balance import Balance
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ..lib.balance_table_update import UpdatetBalanceTable as T

pytestmark = pytest.mark.django_db


def test_income_create():
    obj = IncomeFactory(price=2)

    AccountBalance.objects.all().delete()

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={'incomes.Income': {'incomes': 'account'}}
    )

    actual = AccountBalance.objects.all()

    assert actual.count() == 1
    assert actual[0].account_id == obj.account.id
    assert actual[0].year == 1999
    assert actual[0].past == 0.0
    assert actual[0].incomes == 2.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 2.0
    assert actual[0].have == 0.0
    assert actual[0].delta == -2.0


def test_income_update():
    obj = IncomeFactory(price=2)

    # manually change values in AccountBalance table
    model = AccountBalance.objects.last()
    model.incomes = 0
    model.save()

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={'incomes.Income': {'incomes': 'account'}}
    )

    actual = AccountBalance.objects.all()
    assert actual.count() == 1
    assert actual[0].account_id == obj.account.id
    assert actual[0].year == 1999
    assert actual[0].past == 0.0
    assert actual[0].incomes == 2.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 2.0
    assert actual[0].have == 0.0
    assert actual[0].delta == -2.0


def test_income_delete():
    obj = IncomeFactory(price=2)

    # manually add row in AccountBalance table
    AccountBalanceFactory(account=AccountFactory(title='X'))
    assert AccountBalance.objects.count() == 2

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={'incomes.Income': {'incomes': 'account'}}
    )

    actual = AccountBalance.objects.all()

    assert actual.count() == 1
    assert actual[0].account_id == obj.account.id
    assert actual[0].year == 1999
    assert actual[0].past == 0.0
    assert actual[0].incomes == 2.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 2.0
    assert actual[0].have == 0.0
    assert actual[0].delta == -2.0


def test_income_create_update():
    obj1 = IncomeFactory(date=date(1998, 1, 1), price=4)
    obj2 = IncomeFactory(price=2)

    AccountBalance.objects.get(pk=obj1.pk).delete()

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={'incomes.Income': {'incomes': 'account'}}
    )

    actual = AccountBalance.objects.all()
    assert actual.count() == 2

    actual = AccountBalance.objects.get(account_id=obj2.account.pk, year=1999)
    assert actual.past == 4.0
    assert actual.incomes == 2.0
    assert actual.expenses == 0.0
    assert actual.balance == 6.0
    assert actual.have == 0.0
    assert actual.delta == -6.0

    actual = AccountBalance.objects.get(account_id=obj1.account.pk, year=1998)
    assert actual.past == 0.0
    assert actual.incomes == 4.0
    assert actual.expenses == 0.0
    assert actual.balance == 4.0
    assert actual.have == 0.0
    assert actual.delta == -4.0


def test_income_create_queries(django_assert_num_queries):
    IncomeFactory(account=AccountFactory(title='X'))
    IncomeFactory(account=AccountFactory(title='Y'))
    IncomeFactory(account=AccountFactory(title='Z'))

    AccountBalance.objects.all().delete()

    with django_assert_num_queries(4):
        T(
            category_table='accounts.Account',
            balance_table='accounts.AccountBalance',
            balance_object=Balance,
            hooks={'incomes.Income': {'incomes': 'account'}}
        )


def test_income_create_update_queries(django_assert_num_queries):
    IncomeFactory(price=2)
    obj = IncomeFactory(date=date(1998, 1, 1), price=4)

    AccountBalance.objects.get(pk=obj.pk).delete()

    with django_assert_num_queries(6):
        T(
            category_table='accounts.Account',
            balance_table='accounts.AccountBalance',
            balance_object=Balance,
            hooks={'incomes.Income': {'incomes': 'account'}}
        )


def test_income_expense_create():
    inc = IncomeFactory(price=2)
    exp = ExpenseFactory(price=1)

    AccountBalance.objects.all().delete()

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={
            'incomes.Income': {'incomes': 'account'},
            'expenses.Expense': {'expenses': 'account'},
        }
    )

    actual = AccountBalance.objects.all()

    assert actual.count() == 1
    assert actual[0].account_id == inc.account.id
    assert actual[0].account_id == exp.account.id
    assert actual[0].year == 1999
    assert actual[0].past == 0.0
    assert actual[0].incomes == 2.0
    assert actual[0].expenses == 1.0
    assert actual[0].balance == 1.0
    assert actual[0].have == 0.0
    assert actual[0].delta == -1.0


def test_income_obsolete_rows_must_be_deleted():
    IncomeFactory(price=1)

    # obsolete records
    AccountBalanceFactory(account=AccountFactory(title='X'), year=1974)

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={'incomes.Income': {'incomes': 'account'}}
    )

    actual = AccountBalance.objects.all()

    assert actual.count() == 1
    assert actual[0].year == 1999
    assert actual[0].past == 0.0
    assert actual[0].incomes == 1.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 1.0


def test_income_with_closed_account():
    a = AccountFactory(closed = 1998)

    IncomeFactory(price=1, account=a, date=date(1998, 1, 1))
    IncomeFactory(price=2, account=a, date=date(2000, 1, 1))

    # truncate table
    AccountBalance.objects.all().delete()

    # fake records
    AccountBalanceFactory(year=1998)
    AccountBalanceFactory(year=2000)

    T(
        category_table='accounts.Account',
        balance_table='accounts.AccountBalance',
        balance_object=Balance,
        hooks={'incomes.Income': {'incomes': 'account'}}
    )

    actual = AccountBalance.objects.all()

    assert actual.count() == 2

    assert actual[0].year == 1998
    assert actual[0].past == 0.0
    assert actual[0].incomes == 1.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 1.0

    assert actual[1].year == 2000
    assert actual[1].past == 1.0
    assert actual[1].incomes == 2.0
    assert actual[1].expenses == 0.0
    assert actual[1].balance == 3.0
