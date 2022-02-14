from datetime import date, datetime
from decimal import Decimal

import pytest

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ...journals.models import Journal
from ..factories import IncomeFactory, IncomeTypeFactory
from ..models import Income, IncomeType

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Income Type
# ----------------------------------------------------------------------------
def test_income_type_str():
    i = IncomeTypeFactory.build()

    assert str(i) == 'Income Type'


def test_income_type_items_journal(main_user, second_user):
    IncomeTypeFactory(title='T1', journal=main_user.journal)
    IncomeTypeFactory(title='T2', journal=second_user.journal)

    actual = IncomeType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


def test_income_type_items_journal_queries(django_assert_max_num_queries):
    IncomeTypeFactory()
    with django_assert_max_num_queries(1):
        qs = IncomeType.objects.items().values()



@pytest.mark.xfail
def test_income_type_unique_for_journal(main_user):
    IncomeType.objects.create(title='T', journal=main_user.journal)
    IncomeType.objects.create(title='T', journal=main_user.journal)


def test_income_type_unique_for_journals(main_user, second_user):
    IncomeType.objects.create(title='T', journal=main_user.journal)
    IncomeType.objects.create(title='T', journal=second_user.journal)


# ----------------------------------------------------------------------------
#                                                                       Income
# ----------------------------------------------------------------------------
def test_income_str():
    i = IncomeFactory.build()

    assert str(i) == '1999-01-01: Income Type'


def test_income_related(main_user, second_user):
    t1 = IncomeTypeFactory(title='T1', journal=main_user.journal)
    t2 = IncomeTypeFactory(title='T2', journal=second_user.journal)

    IncomeFactory(income_type=t1)
    IncomeFactory(income_type=t2)

    actual = Income.objects.related()

    assert len(actual) == 1
    assert str(actual[0].income_type) == 'T1'


def test_sum_all_months(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]

    actual = list(Income.objects.sum_by_month(1999))

    assert expect == actual


def test_sum_all_months_ordering(incomes):
    actual = list(Income.objects.sum_by_month(1999))

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[1]['date'] == date(1999, 2, 1)


def test_sum_one_month(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)}
    ]

    actual = list(Income.objects.sum_by_month(1999, 1))

    assert len(expect) == 1
    assert expect == actual


def test_incomes_items():
    IncomeFactory()

    assert len(Income.objects.items()) == 1


def test_incomes_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = Income.objects.items()
        list([x['date'] for x in qs])


def test_incomes_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = Income.objects.year(1999)
        list([x['date'] for x in qs])


def test_incomes_income_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = Income.objects.sum_by_month(1999)
        list([x['date'] for x in qs])


def test_balance(incomes):
    qs = Income.objects.incomes()

    assert qs[0] == {'year': 1970, 'incomes': Decimal('5.25'), 'id': 1}
    assert qs[1] == {'year': 1970, 'incomes': Decimal('4.5'), 'id': 2}
    assert qs[2] == {'year': 1999, 'incomes': Decimal('3.25'), 'id': 1}
    assert qs[3] == {'year': 1999, 'incomes': Decimal('3.5'), 'id': 2}


def test_income_month_type_sum():
    IncomeFactory(
        price=4,
        date=date(1999, 1, 2),
        income_type=IncomeTypeFactory(title='I-2')
    )
    IncomeFactory(
        price=3,
        date=date(1999, 1, 1),
        income_type=IncomeTypeFactory(title='I-2')
    )
    IncomeFactory(
        price=1,
        date=date(1974, 1, 1),
        income_type=IncomeTypeFactory(title='I-1')
    )
    IncomeFactory(
        price=2,
        date=date(1999, 1, 2),
        income_type=IncomeTypeFactory(title='I-1')
    )
    IncomeFactory(
        price=1,
        date=date(1999, 1, 1),
        income_type=IncomeTypeFactory(title='I-1')
    )

    expect = [
        {'date': date(1999, 1, 1), 'title': 'I-1', 'sum': Decimal(3)},
        {'date': date(1999, 1, 1), 'title': 'I-2', 'sum': Decimal(7)},
    ]
    actual = Income.objects.sum_by_month_and_type(1999)

    assert expect == [*actual]


def test_income_new_post_save():
    IncomeFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1000.62
    assert actual['balance'] == 1000.62


def test_income_update_post_save():
    obj = IncomeFactory(price=5)

    # update price
    obj_update = Income.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['balance'] == 1.0


def test_income_post_save_different_accounts():
    IncomeFactory(price=5, account=AccountFactory(title='X'))
    IncomeFactory(price=50, account=AccountFactory(title='Z'))

    actual = AccountBalance.objects.all()

    assert actual.count() == 2


def test_income_post_save_update_with_nothing_changed():
    obj = IncomeFactory(price=5)

    # update price
    obj_update = Income.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 5.0
    assert actual['balance'] == 5.0


def test_income_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title='XXX')

    obj = IncomeFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk)
    assert actual.account.title == 'Account1'
    assert actual.incomes == 5.0
    assert actual.balance == 5.0

    # update account
    obj_new = Income.objects.get(account_id=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    doest_not_exists = False

    try:
        AccountBalance.objects.get(account_id=account_old.pk)
    except AccountBalance.DoesNotExist:
        doest_not_exists = True

    assert doest_not_exists

    actual = AccountBalance.objects.get(account_id=account_new.pk)
    assert actual.account.title == 'XXX'
    assert actual.incomes == 5.0
    assert actual.balance == 5.0


def test_income_post_delete():
    obj = IncomeFactory()
    Income.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    assert actual[0]['title'] == 'Account1'
    assert actual[0]['incomes'] == 0
    assert actual[0]['balance'] == 0

    assert Income.objects.all().count() == 0


def test_income_post_delete_with_update():
    IncomeFactory(price=1)

    obj = IncomeFactory(price=5)
    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 6.0
    assert actual.balance == 6.0

    Income.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 1.0
    assert actual.balance == 1.0

    assert Income.objects.all().count() == 1


def test_income_post_save_update_account_balance_count_qs(django_assert_max_num_queries):
    a = AccountFactory()
    t = IncomeTypeFactory()

    IncomeFactory()

    with django_assert_max_num_queries(5):
        Income.objects.create(
            date=date(1999, 1, 1),
            price=Decimal('2'),
            account=a,
            income_type=t
        )


def test_income_post_save_new_account_balance_count_qs(django_assert_max_num_queries):
    a = AccountFactory()
    t = IncomeTypeFactory()

    AccountBalance.objects.all().delete()

    with django_assert_max_num_queries(24):
        Income.objects.create(
            date = date(1999, 1, 1),
            price = Decimal('2'),
            account = a,
            income_type = t
        )


def test_income_update_post_save_count_qs(django_assert_max_num_queries):
    obj = IncomeFactory(date=date(1999, 1, 1), price=2)

    assert AccountBalance.objects.all().count() == 1

    obj_update = Income.objects.get(pk=obj.pk)
    with django_assert_max_num_queries(6):
        obj_update.price = Decimal('6')
        obj_update.save()

    assert AccountBalance.objects.all().count() == 1

    actual = AccountBalance.objects.last()
    assert actual.incomes == Decimal('6')
    assert actual.balance == Decimal('6')
    assert actual.delta == Decimal('-6')


def test_income_post_save_first_year_record():
    obj1 = IncomeFactory(date=date(1974, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    obj2 = IncomeFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj2.account.pk, year=1999)
    assert actual.past == Decimal('5')
    assert actual.incomes == Decimal('1')
    assert actual.expenses == Decimal('0')
    assert actual.balance == Decimal('6')
    assert actual.delta == Decimal('-6')

    actual = AccountBalance.objects.get(account_id=obj1.account.pk, year=1974)
    assert actual.past == Decimal('0')
    assert actual.incomes == Decimal('5')
    assert actual.expenses == Decimal('0')
    assert actual.balance == Decimal('5')
    assert actual.delta == Decimal('-5')


def test_income_post_save_update_balance_row():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    obj = IncomeFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)

    assert actual.past == Decimal('5')
    assert actual.incomes == Decimal('1')
    assert actual.expenses == Decimal('0')
    assert actual.balance == Decimal('6')
    assert actual.delta == Decimal('-6')


def test_income_post_delete_new_signal():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    obj = IncomeFactory(date=date(1999, 1, 1), price=1)

    # check before delete
    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == Decimal('5')
    assert actual.incomes == Decimal('1')
    assert actual.expenses == Decimal('0')
    assert actual.balance == Decimal('6')
    assert actual.delta == Decimal('-6')

    # delete Income object
    Income.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == Decimal('5')
    assert actual.incomes == Decimal('0')
    assert actual.expenses == Decimal('0')
    assert actual.balance == Decimal('5')
    assert actual.delta == Decimal('-5')


def test_income_post_delete_empty_account_balance_table():
    obj_stay = IncomeFactory(date=date(1974, 1, 1), price=5)
    obj_del = IncomeFactory(date=date(1999, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    # delete Income object
    Income.objects.get(pk=obj_del.pk).delete()

    actual = AccountBalance.objects.all()

    assert actual.count() == 1
    assert actual[0].account_id == obj_stay.account.pk
    assert actual[0].id == 3
    assert actual[0].year == 1974
    assert actual[0].past == Decimal('0')
    assert actual[0].incomes == Decimal('5')
    assert actual[0].expenses == Decimal('0')
    assert actual[0].balance == Decimal('5')
    assert actual[0].delta == Decimal('-5')


def test_income_years_sum():
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)

    actual = Income.objects.sum_by_year()

    assert actual[0]['year'] == 1998
    assert actual[0]['sum'] == 8.0

    assert actual[1]['year'] == 1999
    assert actual[1]['sum'] == 10.0


def test_income_year_sum_count_qs(django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        list([x['year'] for x in Income.objects.sum_by_year()])


def test_income_year_sum_filter():
    IncomeFactory(
        date=date(1999, 1, 1),
        price=5.0,
        income_type=IncomeTypeFactory(title='x', type='s'))
    IncomeFactory(
        date=date(1999, 1, 1),
        price=5.0,
        income_type=IncomeTypeFactory(title='xx', type='s'))
    IncomeFactory(
        date=date(1999, 1, 1),
        price=15.0,
        income_type=IncomeTypeFactory(title='xxx', type='o'))

    actual = Income.objects.sum_by_year(['s'])

    assert actual[0]['year'] == 1999
    assert actual[0]['sum'] == 10.0


def test_income_year_sum_filter_two_types():
    IncomeFactory(
        date=date(1999, 1, 1),
        price=5.0,
        income_type=IncomeTypeFactory(title='1', type='x'))
    IncomeFactory(
        date=date(1999, 1, 1),
        price=5.0,
        income_type=IncomeTypeFactory(title='2', type='x'))
    IncomeFactory(
        date=date(1999, 1, 1),
        price=15.0,
        income_type=IncomeTypeFactory(title='3', type='y'))
    IncomeFactory(
        date=date(1999, 1, 1),
        price=20.0,
        income_type=IncomeTypeFactory(title='4', type='z'))

    actual = Income.objects.sum_by_year(['x', 'y'])

    assert actual[0]['year'] == 1999
    assert actual[0]['sum'] == 25.0


def test_income_year_sum_filter_count_qs(django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        list([x['year'] for x in Income.objects.sum_by_year(['x'])])


def test_income_updates_journal_first_record():
    assert Journal.objects.first().first_record == date(1999, 1, 1)

    IncomeFactory(date=date(1974, 2, 2))

    assert Journal.objects.first().first_record == date(1974, 2, 2)
