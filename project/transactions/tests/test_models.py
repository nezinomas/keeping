from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountBalance, AccountFactory
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingTypeFactory
from ...savings.models import SavingBalance
from ...users.factories import UserFactory
from ..factories import (SavingChangeFactory, SavingCloseFactory,
                         TransactionFactory)
from ..models import SavingChange, SavingClose, Transaction

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_str():
    t = TransactionFactory.build()

    assert str(t) == '1999-01-01 Account1->Account2: 200'


def test_transaction_related(main_user, second_user):
    t1 = AccountFactory(title='T1', journal=main_user.journal)
    f1 = AccountFactory(title='F1', journal=main_user.journal)

    t2 = AccountFactory(title='T2', journal=second_user.journal)
    f2 = AccountFactory(title='F2', journal=second_user.journal)

    TransactionFactory(to_account=t1, from_account=f1)
    TransactionFactory(to_account=t2, from_account=f2)

    actual = Transaction.objects.related()

    assert len(actual) == 1
    assert str(actual[0].from_account) == 'F1'
    assert str(actual[0].to_account) == 'T1'


def test_transaction_items(main_user, second_user):
    t1 = AccountFactory(title='T1', journal=main_user.journal)
    f1 = AccountFactory(title='F1', journal=main_user.journal)

    t2 = AccountFactory(title='T2', journal=second_user.journal)
    f2 = AccountFactory(title='F2', journal=second_user.journal)

    TransactionFactory(to_account=t1, from_account=f1)
    TransactionFactory(to_account=t2, from_account=f2)

    actual = Transaction.objects.related()

    assert len(actual) == 1
    assert str(actual[0].from_account) == 'F1'
    assert str(actual[0].to_account) == 'T1'


def test_transaction_year(second_user):
    a = AccountFactory(title='T1', journal=second_user.journal)

    TransactionFactory(date=date(1999, 1, 1))
    TransactionFactory(date=date(2000, 1, 1))
    TransactionFactory(date=date(2000, 1, 1), from_account=a)

    actual = Transaction.objects.year(1999)

    assert actual.count() == 1


def test_transaction_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(Transaction.objects.items())


def test_transaction_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(Transaction.objects.year(1999))


def test_transaction_summary_from(transactions):
    expect = [{
        'title': 'Account1',
        'tr_from_past': 1.25,
        'tr_from_now': 4.5,
    }, {
        'title': 'Account2',
        'tr_from_past': 5.25,
        'tr_from_now': 3.25,
    }]

    actual = list(
        Transaction.objects
        .summary_from(1999)
        .order_by('from_account__title')
    )

    assert expect == actual


def test_transaction_summary_to(transactions):
    expect = [{
        'title': 'Account1',
        'tr_to_past': 5.25,
        'tr_to_now': 3.25,
    }, {
        'title': 'Account2',
        'tr_to_past': 1.25,
        'tr_to_now': 4.5,
    }]

    actual = list(
        Transaction.objects
        .summary_to(1999).order_by('to_account__title'))

    assert expect == actual


def test_transaction_new_post_save():
    TransactionFactory()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2

    assert actual[0].account.title == 'Account2'
    assert actual[0].incomes == 200.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 200.0
    assert actual[0].delta == -200

    assert actual[1].account.title == 'Account1'
    assert actual[1].incomes == 0.0
    assert actual[1].expenses == 200.0
    assert actual[1].balance == -200.0
    assert actual[1].delta == 200


def test_transaction_update_post_save():
    a_from = AccountFactory(title='From')
    a_to = AccountFactory(title='To')

    obj = TransactionFactory(date=date(1999, 1, 1),
                            from_account=a_from,
                            to_account=a_to,
                            price=100)

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.price = 10
    obj_update.save()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2

    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.incomes == 10.0
    assert actual.expenses == 0.0
    assert actual.balance == 10.0
    assert actual.delta == -10

    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.incomes == 0.0
    assert actual.expenses == 10.0
    assert actual.balance == -10.0
    assert actual.delta == 10


def test_transaction_post_save_first_record():
    a_from = AccountFactory(title='From')
    a_to = AccountFactory(title='To')

    # past records
    IncomeFactory(account=a_from, date=date(1998, 1, 1), price=6)
    ExpenseFactory(account=a_from, date=date(1998, 1, 1), price=5)

    IncomeFactory(account=a_to, date=date(1998, 1, 1), price=5)
    ExpenseFactory(account=a_to, date=date(1998, 1, 1), price=3)

    # truncate AccountBalace
    AccountBalance.objects.all().delete()

    TransactionFactory(date=date(1999, 1, 1),
                       from_account=a_from,
                       to_account=a_to,
                       price=1)

    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 2.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 3.0
    assert actual.delta == -3.0

    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.past == 1.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == 0.0
    assert actual.delta == 0.0


def test_transaction_post_save_new():
    a_from = AccountFactory(title='From')
    a_to = AccountFactory(title='To')

    # past records
    IncomeFactory(account=a_from, date=date(1998, 1, 1), price=6)
    ExpenseFactory(account=a_from, date=date(1998, 1, 1), price=5)

    IncomeFactory(account=a_to, date=date(1998, 1, 1), price=5)
    ExpenseFactory(account=a_to, date=date(1998, 1, 1), price=3)

    TransactionFactory(date=date(1999, 1, 1),
                       from_account=a_from,
                       to_account=a_to,
                       price=1)

    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 2.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 3.0
    assert actual.delta == -3.0

    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.past == 1.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == 0.0
    assert actual.delta == 0.0


def test_transaction_post_delete():
    u = TransactionFactory()
    u.delete()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2

    assert actual[0].account.title == 'Account2'
    assert actual[0].incomes == 0
    assert actual[0].expenses == 0
    assert actual[0].balance == 0
    assert actual[0].delta == 0

    assert actual[1].account.title == 'Account1'
    assert actual[1].incomes == 0
    assert actual[1].expenses == 0
    assert actual[1].balance == 0
    assert actual[1].delta == 0

    assert Transaction.objects.all().count() == 0


def test_transaction_post_delete_with_update():
    TransactionFactory(price=10)

    u = TransactionFactory()
    u.delete()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2

    assert actual[0].account.title == 'Account2'
    assert actual[0].incomes == 10.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 10.0
    assert actual[0].delta == -10

    assert actual[1].account.title == 'Account1'
    assert actual[1].incomes == 0.0
    assert actual[1].expenses == 10.0
    assert actual[1].balance == -10.0
    assert actual[1].delta == 10

    assert Transaction.objects.all().count() == 1


def test_transactions_from_db_classmethod():
    _from = AccountFactory(title='X')
    _to = AccountFactory(title='Y')

    TransactionFactory(from_account=_from, to_account=_to)

    obj = Transaction.objects.last()

    expect = {'account_id': [_from.pk, _to.pk]}

    assert obj._old_values == expect


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_str():
    s = SavingCloseFactory.build()

    assert str(s) == '1999-01-01 Savings From->Account To: 10'


def test_saving_close_related(main_user, second_user):
    a1 = AccountFactory(title='A1', journal=main_user.journal)
    a2 = AccountFactory(title='A2', journal=second_user.journal)

    s1 = SavingTypeFactory(title='S1', journal=main_user.journal)
    s2 = SavingTypeFactory(title='S2', journal=second_user.journal)

    SavingCloseFactory(to_account=a1, from_account=s1)
    SavingCloseFactory(to_account=a2, from_account=s2)

    actual = SavingClose.objects.related()

    assert len(actual) == 1
    assert str(actual[0].from_account) == 'S1'
    assert str(actual[0].to_account) == 'A1'


def test_saving_close_month_sums(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.sum_by_month(1999))

    assert expect == actual


def test_saving_close_month_sums_only_january(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.sum_by_month(1999, 1))

    assert expect == actual


def test_saving_close_month_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(SavingClose.objects.sum_by_month(1999))


def test_saving_close_summary_from(savings_close):
    expect = [{
        'title': 'Saving1',
        's_close_from_past': Decimal('0.25'),
        's_close_from_now': Decimal('0.25'),
        's_close_from_fee_now': Decimal('0.05'),
        's_close_from_fee_past': Decimal('0.05'),
    }]

    actual = list(
        SavingClose.objects
        .summary_from(1999).order_by('from_account__title'))

    assert expect == actual


def test_saving_close_summary_to(savings_close):
    expect = [{
        'title': 'Account1',
        's_close_to_past': 0.25,
        's_close_to_now': 0.25,
    }, {
        'title': 'Account2',
        's_close_to_past': 0.0,
        's_close_to_now': 0.0,
    }]

    actual = list(
        SavingClose.objects
        .summary_to(1999)
        .order_by('to_account__title')
    )

    assert expect == actual


def test_saving_close_new_post_save():
    SavingCloseFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['incomes'] == 10.0
    assert actual[0]['balance'] == 10.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == 0.0


def test_saving_close_update_post_save():
    obj = SavingCloseFactory()

    # update price
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['incomes'] == 1.0
    assert actual[0]['balance'] == 1.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == 0.0


def test_saving_close_post_delete():
    obj = SavingCloseFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['incomes'] == 0
    assert actual[0]['balance'] == 0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 0
    assert actual[0]['fees'] == 0
    assert actual[0]['incomes'] == 0

    assert SavingClose.objects.all().count() == 0


def test_saving_close_post_delete_with_update():
    SavingCloseFactory(price=1)

    obj = SavingCloseFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['incomes'] == 1.0
    assert actual[0]['balance'] == 1.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == 0.0

    assert SavingClose.objects.all().count() == 1


def test_saving_close_from_db_classmethod():
    _from = SavingTypeFactory(title='X')
    _to = AccountFactory(title='Y')

    SavingCloseFactory(from_account=_from, to_account=_to)

    obj = SavingClose.objects.last()

    expect = {'account_id': [_to.pk], 'saving_type_id': [_from.pk]}

    assert obj._old_values == expect


# ----------------------------------------------------------------------------
#                                                                 Saving Change
# ----------------------------------------------------------------------------
def test_savings_change_str():
    s = SavingChangeFactory.build()

    assert str(s) == '1999-01-01 Savings From->Savings To: 10'


def test_saving_change_related(main_user, second_user):
    f1 = SavingTypeFactory(title='F1', journal=main_user.journal)
    f2 = SavingTypeFactory(title='F2', journal=second_user.journal)

    t1 = SavingTypeFactory(title='T1', journal=main_user.journal)
    t2 = SavingTypeFactory(title='T2', journal=second_user.journal)

    SavingChangeFactory(from_account=f1, to_account=t1)
    SavingChangeFactory(from_account=f2, to_account=t2)

    actual = SavingChange.objects.related()

    assert len(actual) == 1
    assert str(actual[0].from_account) == 'F1'
    assert str(actual[0].to_account) == 'T1'


def test_saving_change_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(SavingChange.objects.items())


def test_savings_change_summary_from(savings_change):
    expect = [{
        'title': 'Saving1',
        's_change_from_past': 2.25,
        's_change_from_now': 1.25,
        's_change_from_fee_past': 0.15,
        's_change_from_fee_now': 0.05,
    }]

    actual = list(
        SavingChange.objects
        .summary_from(1999).order_by('from_account__title'))

    assert_(expect, actual)


def test_savings_change_summary_to(savings_change):
    expect = [{
        's_change_to_past': Decimal(2.25),
        's_change_to_now': Decimal(1.25),
    }]

    actual = list(
        SavingChange.objects
        .summary_to(1999).order_by('to_account__title'))

    assert_(expect, actual)


def test_saving_change_new_post_save():
    SavingChangeFactory()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == 0.0

    assert actual[1]['title'] == 'Savings To'
    assert actual[1]['invested'] == 10.0
    assert actual[1]['fees'] == 0.0
    assert actual[1]['incomes'] == 10.0


def test_saving_change_update_post_save():
    obj = SavingChangeFactory()

    # update price
    obj.price = 1
    obj.save()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == 0.0

    assert actual[1]['title'] == 'Savings To'
    assert actual[1]['invested'] == 1.0
    assert actual[1]['fees'] == 0.0
    assert actual[1]['incomes'] == 1.0


def test_saving_change_post_delete():
    obj = SavingChangeFactory()
    obj.delete()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['invested'] == 0
    assert actual[0]['fees'] == 0
    assert actual[0]['incomes'] == 0

    assert actual[1]['title'] == 'Savings To'
    assert actual[1]['invested'] == 0
    assert actual[1]['fees'] == 0
    assert actual[1]['incomes'] == 0

    assert SavingChange.objects.all().count() == 0


def test_saving_change_post_delete_with_update():
    SavingChangeFactory(price=1)

    obj = SavingChangeFactory()
    obj.delete()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == 0.0

    assert actual[1]['title'] == 'Savings To'
    assert actual[1]['invested'] == 1.0
    assert actual[1]['fees'] == 0.0
    assert actual[1]['incomes'] == 1.0

    assert SavingChange.objects.all().count() == 1


def test_saving_change_from_db_classmethod():
    _from = SavingTypeFactory(title='X')
    _to = SavingTypeFactory(title='Y')

    SavingChangeFactory(from_account=_from, to_account=_to)

    obj = SavingChange.objects.last()

    expect = {'saving_type_id': [_from.pk, _to.pk]}

    assert obj._old_values == expect
