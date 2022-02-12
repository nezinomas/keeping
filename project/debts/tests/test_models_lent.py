from datetime import date as dt
from decimal import Decimal

import pytest

from ...accounts.factories import AccountBalance, AccountFactory
from ...incomes.factories import IncomeFactory
from ...journals.factories import JournalFactory
from ..factories import DebtFactory
from ..models import Debt

pytestmark = pytest.mark.django_db


def test_debt_str():
    v = DebtFactory.build(name='X')

    assert str(v) == 'X'


def test_debt_fields():
    assert Debt._meta.get_field('date')
    assert Debt._meta.get_field('name')
    assert Debt._meta.get_field('price')
    assert Debt._meta.get_field('returned')
    assert Debt._meta.get_field('closed')
    assert Debt._meta.get_field('account')
    assert Debt._meta.get_field('journal')
    assert Debt._meta.get_field('remark')


def test_debt_related(second_user):
    o = DebtFactory()
    DebtFactory(journal=second_user.journal)

    actual = Debt.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == str(o)


def test_debt_related_queries(django_assert_num_queries):
    DebtFactory()
    DebtFactory()

    with django_assert_num_queries(1):
        a = [x.account.title for x in list(Debt.objects.related())]


def test_debt_sort():
    o1 = DebtFactory(date=dt(1999, 1, 2))
    o2 = DebtFactory(date=dt(1999, 12, 13))

    actual = Debt.objects.related()

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


def test_debt_items(second_user):
    o = DebtFactory()
    DebtFactory(name='X1', journal=second_user.journal)

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert str(actual[0]) == str(o)


def test_debt_year():
    o = DebtFactory(name='N1', date=dt(1999, 2, 3))
    DebtFactory(name='N2', date=dt(2999, 2, 3), price=2)

    actual = Debt.objects.year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == str(o)
    assert actual[0].name == o.name
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == Decimal('100')


def test_debt_year_and_not_closed():
    o1 = DebtFactory(date=dt(1974, 1, 1), closed=False)
    DebtFactory(date=dt(1974, 12, 1), closed=True)
    o2 = DebtFactory(date=dt(1999, 1, 1), closed=False)
    o3 = DebtFactory(date=dt(1999, 12, 1), closed=True)

    actual = Debt.objects.year(1999)

    assert actual.count() == 3

    assert actual[0].date == o3.date
    assert actual[1].date == o2.date
    assert actual[2].date == o1.date


def test_debt_new_post_save():
    DebtFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 100.0


def test_debt_update_post_save():
    obj = DebtFactory()

    # update object
    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0


def test_borrow_post_save_first_record():
    a = AccountFactory()
    j = JournalFactory()

    # past records
    IncomeFactory(date=dt(1998, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    Debt.objects.create(
        date=dt(1999, 1, 1),
        price=1,
        account=a,
        journal=j
    )

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 5.0
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 6.0


def test_debt_post_save_update_with_nothing_changed():
    obj = DebtFactory(price=5)

    # update price
    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 5.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 5.0


def test_debt_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title='XXX')

    obj = DebtFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk)
    assert actual.account.title == 'Account1'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    # update price
    obj_new = Debt.objects.get(account_id=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=account_old.pk)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=account_new.pk)
    assert actual.account.title == 'XXX'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0


def test_debt_post_delete():
    obj = DebtFactory()

    Debt.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0
    assert actual['expenses'] == 0
    assert actual['balance'] == 0


def test_debt_post_delete_with_updt():
    DebtFactory(price=1)

    obj = DebtFactory()
    Debt.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0

    assert Debt.objects.all().count() == 1


def test_debt_unique_users(main_user, second_user):
    DebtFactory(name='T1', journal=main_user.journal)
    DebtFactory(name='T1', journal=second_user.journal)


def test_debt_sum_all_months():
    DebtFactory(date=dt(1999, 1, 1), price=1, returned=0.5)
    DebtFactory(date=dt(1999, 1, 2), price=2, returned=0.5)
    DebtFactory(date=dt(1999, 2, 1), price=4, returned=1)
    DebtFactory(date=dt(1999, 2, 2), price=1, returned=0.5)
    DebtFactory(date=dt(1999, 1, 1), closed=True)
    DebtFactory(date=dt(1974, 1, 1))

    expect = [
        {'date': dt(1999, 1, 1), 'sum_debt': Decimal('3'), 'sum_return': Decimal('1')},
        {'date': dt(1999, 2, 1), 'sum_debt': Decimal('5'), 'sum_return': Decimal('1.5')},
    ]

    actual = list(Debt.objects.sum_by_month(1999))

    assert expect == actual


def test_debt_sum_all_months_ordering(second_user):
    DebtFactory(date=dt(1999, 1, 1), price=1)
    DebtFactory(date=dt(1999, 1, 2), price=2)
    DebtFactory(date=dt(1999, 1, 2), price=2, journal=second_user.journal)
    DebtFactory(date=dt(1999, 2, 1), price=4)
    DebtFactory(date=dt(1999, 2, 2), price=1)
    DebtFactory(date=dt(1999, 2, 2), price=6, journal=second_user.journal)

    actual = list(Debt.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


def test_debt_sum_all_not_closed():
    DebtFactory(date=dt(1999, 1, 1), price=12, closed=True)
    DebtFactory(date=dt(1999, 1, 1), price=1, returned=0.5)
    DebtFactory(date=dt(1999, 1, 2), price=1, returned=0.5)
    DebtFactory(date=dt(1974, 1, 2), price=3, returned=2)

    expect = {'debt': Decimal('5'), 'debt_return': Decimal('3')}

    actual = Debt.objects.sum_all()

    assert expect == actual


def test_debt_incomes():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    DebtFactory(date=dt(1970, 1, 1), account=a1, price=1)
    DebtFactory(date=dt(1970, 1, 1), account=a1, price=2)
    DebtFactory(date=dt(1970, 1, 1), account=a2, price=3)
    DebtFactory(date=dt(1970, 1, 1), account=a2, price=4)

    DebtFactory(date=dt(1999, 1, 1), account=a1, price=10)
    DebtFactory(date=dt(1999, 1, 1), account=a1, price=20)
    DebtFactory(date=dt(1999, 1, 1), account=a2, price=30)
    DebtFactory(date=dt(1999, 1, 1), account=a2, price=40)

    actual = Debt.objects.incomes()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['incomes'] == 3

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['incomes'] == 7

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['incomes'] == 30

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['incomes'] == 70
