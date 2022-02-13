from datetime import date as dt
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...incomes.factories import IncomeFactory
from ..factories import DebtFactory, DebtReturnFactory
from ..models import Debt, DebtReturn

pytestmark = pytest.mark.django_db


def test_debt_return_str():
    v = DebtReturnFactory.build()

    assert str(v) == 'Grąžino 5.0'


def test_debt_return_fields():
    assert DebtReturn._meta.get_field('date')
    assert DebtReturn._meta.get_field('price')
    assert DebtReturn._meta.get_field('account')
    assert DebtReturn._meta.get_field('debt')
    assert DebtReturn._meta.get_field('remark')


def test_debt_return_related(main_user, second_user):
    b1 = DebtFactory(name='B1', price=1, journal=main_user.journal)
    b2 = DebtFactory(name='B2', price=2, journal=second_user.journal)

    DebtReturnFactory(debt=b1, price=1.1)
    DebtReturnFactory(debt=b2, price=2.1)

    actual = DebtReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžino 1.1'


def test_debt_return_related_queries(django_assert_num_queries):
    DebtReturnFactory()
    DebtReturnFactory()

    with django_assert_num_queries(1):
        a = [x.account.title for x in list(DebtReturn.objects.related())]


def test_debt_return_items():
    DebtReturnFactory()
    DebtReturnFactory()

    actual = DebtReturn.objects.items()

    assert actual.count() == 2


def test_debt_return_year():
    DebtReturnFactory()
    DebtReturnFactory(date=dt(1974, 1, 2))

    actual = DebtReturn.objects.year(1999)

    assert actual.count() == 1


def test_debt_return_new_record_updates_debt_tbl():
    DebtReturnFactory()

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')


def test_debt_return_update():
    obj = DebtReturnFactory()

    actual = Debt.objects.items()
    assert actual[0].returned == Decimal('30')

    obj.price = Decimal('20')
    obj.save()

    assert DebtReturn.objects.items().count() == 1

    actual = Debt.objects.items()
    assert actual[0].returned == Decimal('45')


def test_debt_return_new_record_updates_debt_tbl_empty_returned_field():
    DebtReturnFactory(debt=DebtFactory(returned=None))

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('5')


@patch('project.debts.models.Debt.objects.get')
def test_debt_return_new_record_updates_debt_tbl_error_on_save_parent(mck):
    mck.side_effect = TypeError

    try:
        DebtReturnFactory()
    except:
        pass

    actual = Debt.objects.items()
    assert actual[0].returned == Decimal('25')

    actual = DebtReturn.objects.all()
    assert actual.count() == 0


def test_debt_return_delete_record_updates_debt_tbl():
    obj = DebtReturnFactory()

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')

    obj.delete()

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('25')


def test_debt_return_delete_record_updates_debt_tbl_error_on_save():
    obj = DebtReturnFactory()

    actual = Debt.objects.items()

    assert actual[0].returned == Decimal('30')

    with patch('project.debts.models.super') as mck:
        mck.side_effect = TypeError

        try:
            obj.delete()
        except:
            pass

    actual = Debt.objects.items()

    assert actual[0].returned == Decimal('30')


def test_debt_return_new_post_save():
    DebtReturnFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]
    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 5.0
    assert actual['balance'] == 95.0


def test_debt_return_update_post_save():
    obj = DebtReturnFactory()

    # update object
    obj_update = DebtReturn.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == 99.0


def test_debt_return_post_save_first_record():
    l = DebtFactory(price=5)

    IncomeFactory(date=dt(1998, 1, 1), price=1)

    # truncate AccountBalance table
    AccountBalance.objects.all().delete()

    DebtReturnFactory(date=dt(1999, 1, 1), debt=l, price=2)

    actual = AccountBalance.objects.items()

    assert actual[0].year == 1998
    assert actual[0].past == 0.0
    assert actual[0].incomes == 1.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 1.0
    assert actual[0].delta == -1.0

    assert actual[1].year == 1999
    assert actual[1].past == 1.0
    assert actual[1].incomes == 5.0
    assert actual[1].expenses == 2.0
    assert actual[1].balance == 4.0
    assert actual[1].delta == -4.0


def test_debt_return_post_delete():
    obj = DebtReturnFactory()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 5.0
    assert actual.balance == 95.0

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 0.0
    assert actual.balance == 100.0


def test_debt_return_post_delete_with_updt():
    b = DebtFactory()
    DebtReturnFactory(debt=b, price=1)

    obj = DebtReturnFactory(debt=b, price=2)

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 3.0
    assert actual.balance == 97.0

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 1.0
    assert actual.balance == 99.0


def test_debt_return_sum_all_months():
    DebtReturnFactory(date=dt(1999, 1, 1), price=1)
    DebtReturnFactory(date=dt(1999, 1, 2), price=2)
    DebtReturnFactory(date=dt(1999, 2, 1), price=4)
    DebtReturnFactory(date=dt(1999, 2, 2), price=1)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')},
        {'date': dt(1999, 2, 1), 'sum': Decimal('5')},
    ]

    actual = list(DebtReturn.objects.sum_by_month(1999))

    assert expect == actual


def test_debt_return_sum_all_months_ordering():
    DebtReturnFactory(date=dt(1999, 1, 1), price=1)
    DebtReturnFactory(date=dt(1999, 1, 2), price=2)
    DebtReturnFactory(date=dt(1999, 2, 1), price=4)
    DebtReturnFactory(date=dt(1999, 2, 2), price=1)

    actual = list(DebtReturn.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


def test_debt_return_sum_one_month():
    DebtReturnFactory(date=dt(1999, 1, 1), price=1)
    DebtReturnFactory(date=dt(1999, 1, 2), price=2)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')}
    ]

    actual = list(DebtReturn.objects.sum_by_month(1999, 1))

    assert len(expect) == 1
    assert expect == actual


def test_debt_return_autoclose():
    DebtReturnFactory(price=75)

    actual = Debt.objects.first()

    assert actual.returned == Decimal('100')
    assert actual.closed


def test_debt_return_expenses():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    DebtReturnFactory(date=dt(1970, 1, 1), account=a1, price=1)
    DebtReturnFactory(date=dt(1970, 1, 1), account=a1, price=2)
    DebtReturnFactory(date=dt(1970, 1, 1), account=a2, price=3)
    DebtReturnFactory(date=dt(1970, 1, 1), account=a2, price=4)

    DebtReturnFactory(date=dt(1999, 1, 1), account=a1, price=10)
    DebtReturnFactory(date=dt(1999, 1, 1), account=a1, price=20)
    DebtReturnFactory(date=dt(1999, 1, 1), account=a2, price=30)
    DebtReturnFactory(date=dt(1999, 1, 1), account=a2, price=40)

    actual = DebtReturn.objects.expenses()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['expenses'] == 3

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['expenses'] == 7

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['expenses'] == 30

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['expenses'] == 70
