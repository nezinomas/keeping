from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from project.accounts.models import Account

from project.journals.factories import JournalFactory

from ...accounts.factories import AccountBalance, AccountFactory
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory, SavingTypeFactory
from ...savings.models import SavingBalance
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

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == 'To'
    assert actual.past == 2.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 3.0
    assert actual.delta == -3.0

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == 'From'
    assert actual.past == 1.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == 0.0
    assert actual.delta == 0.0

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1998)
    assert actual.account.title == 'To'
    assert actual.past == 0.0
    assert actual.incomes == 5.0
    assert actual.expenses == 3.0
    assert actual.balance == 2.0
    assert actual.delta == -2.0

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1998)
    assert actual.account.title == 'From'
    assert actual.past == 0.0
    assert actual.incomes == 6.0
    assert actual.expenses == 5.0
    assert actual.balance == 1.0
    assert actual.delta == -1.0


def test_transaction_post_save_new(get_user):
    # ToDo: after refactore signals, remove get_user
    get_user.year = 1998

    a_from = AccountFactory(title='From')
    a_to = AccountFactory(title='To')

    # past records
    IncomeFactory(date=date(1998, 1, 1), account=a_from, price=6)
    ExpenseFactory(date=date(1998, 1, 1), account=a_from, price=5)

    IncomeFactory(date=date(1998, 1, 1), account=a_to, price=5)
    ExpenseFactory(date=date(1998, 1, 1), account=a_to, price=3)

    TransactionFactory(date=date(1999, 1, 1),
                       from_account=a_from,
                       to_account=a_to,
                       price=1)

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == 'To'
    assert actual.past == 2.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 3.0
    assert actual.delta == -3.0

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == 'From'
    assert actual.past == 1.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == 0.0
    assert actual.delta == 0.0


def test_transaction_post_save_update_with_nothing_changed():
    a_from = AccountFactory(title='From')
    a_to = AccountFactory(title='To')

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0


    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_transaction_post_save_change_from_account():
    a_from = AccountFactory(title='From')
    a_from_new = AccountFactory(title='From-New')
    a_to = AccountFactory(title='To')

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)
    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.from_account = a_from_new
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=a_from.pk)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=a_from_new.pk)
    assert actual.account.title == 'From-New'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_transaction_post_save_change_to_account():
    a_from = AccountFactory(title='From')
    a_to = AccountFactory(title='To')
    a_to_new = AccountFactory(title='To-New')

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)

    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.to_account = a_to_new
    obj_update.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=a_to.pk)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=a_to_new.pk)
    assert actual.account.title == 'To-New'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_transaction_post_save_change_from_and_to_account():
    a_from = AccountFactory(title='From')
    a_from_new = AccountFactory(title='From-New')
    a_to = AccountFactory(title='To')
    a_to_new = AccountFactory(title='To-New')

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)

    # from_account
    actual = AccountBalance.objects.get(account_id=a_from.pk)
    assert actual.account.title == 'From'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0

    # to_account
    actual = AccountBalance.objects.get(account_id=a_to.pk)
    assert actual.account.title == 'To'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    # update from and to
    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.to_account = a_to_new
    obj_update.from_account = a_from_new
    obj_update.save()

    # to_account old
    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=a_to.pk)
    except AccountBalance.DoesNotExist:
        fail = True
    assert fail

    # to_account new
    actual = AccountBalance.objects.get(account_id=a_to_new.pk)
    assert actual.account.title == 'To-New'
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    # from_account old
    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=a_from.pk)
    except AccountBalance.DoesNotExist:
        fail = True
    assert fail

    # from_account new
    actual = AccountBalance.objects.get(account_id=a_from_new.pk)
    assert actual.account.title == 'From-New'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_transaction_post_delete():
    obj = TransactionFactory()

    Transaction.objects.get(pk=obj.pk).delete()

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

    obj = TransactionFactory()
    Transaction.objects.get(pk=obj.pk).delete()

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


def test_transaction_balance_incomes(transactions):
    actual = Transaction.objects.incomes()

    # 1974
    assert actual[0]['year'] == 1970
    assert actual[0]['incomes'] == 5.25
    assert actual[0]['id'] == 1

    assert actual[1]['year'] == 1970
    assert actual[1]['incomes'] == 1.25
    assert actual[1]['id'] == 2

    # 1999
    assert actual[2]['year'] == 1999
    assert actual[2]['incomes'] == 3.25
    assert actual[2]['id'] == 1

    assert actual[3]['year'] == 1999
    assert actual[3]['incomes'] == 4.5
    assert actual[3]['id'] == 2


def test_transaction_balance_expenses(transactions):
    actual = Transaction.objects.expenses()

    # 1974
    assert actual[0]['year'] == 1970
    assert actual[0]['expenses'] == 1.25
    assert actual[0]['id'] == 1

    assert actual[1]['year'] == 1970
    assert actual[1]['expenses'] == 5.25
    assert actual[1]['id'] == 2

    # 1999
    assert actual[2]['year'] == 1999
    assert actual[2]['expenses'] == 4.5
    assert actual[2]['id'] == 1

    assert actual[3]['year'] == 1999
    assert actual[3]['expenses'] == 3.25
    assert actual[3]['id'] == 2


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


def test_saving_close_post_save():
    SavingCloseFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 10.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 10.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['invested'] == 0.0
    assert actual[0]['incomes'] == -10.0


def test_saving_close_post_save_update():
    obj = SavingCloseFactory()

    # update price
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.year(1999)
    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 1.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 1.0

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 1
    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['invested'] == 0.0
    assert actual[0]['incomes'] == -1.0


def test_saving_close_post_save_first_record():
    _to = AccountFactory(title='To')
    _from = SavingTypeFactory(title='From')

    SavingFactory(saving_type=_from, price=4, date=date(1998, 1, 1), fee=0.25)
    IncomeFactory(account=_to, price=1, date=date(1998, 1, 1))

    # truncate table
    SavingBalance.objects.all().delete()
    AccountBalance.objects.all().delete()

    SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == 'To'
    assert actual.past == 1.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 2.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 4.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.5
    assert actual.invested == 2.5
    assert actual.incomes == 3.0


def test_saving_close_post_save_new():
    _to = AccountFactory(title='To')
    _from = SavingTypeFactory(title='From')

    SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.year(1999)
    assert actual.count() == 1

    actual = AccountBalance.objects.get(account_id=_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_close_post_save_nothing_changed():
    _to = AccountFactory(title='To')
    _from = SavingTypeFactory(title='From')

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.save()

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 1

    actual = AccountBalance.objects.year(1999)
    assert actual.count() == 1

    actual = AccountBalance.objects.get(account_id=_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_close_post_save_changed_from():
    _to = AccountFactory(title='To')
    _from = SavingTypeFactory(title='From')
    _from_new = SavingTypeFactory(title='From-New')

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)
    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.from_account = _from_new
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk)
    assert actual.saving_type.title == 'From-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_close_post_save_changed_to():
    _to = AccountFactory(title='To')
    _to_new = AccountFactory(title='To-New')
    _from = SavingTypeFactory(title='From')

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.get(account_id=_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=_to.pk)
    except AccountBalance.DoesNotExist:
        fail = True
    assert fail

    actual = AccountBalance.objects.get(account_id=_to_new.pk)
    assert actual.account.title == 'To-New'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_close_post_save_changed_from_and_to():
    _to = AccountFactory(title='To')
    _to_new = AccountFactory(title='To-New')
    _from = SavingTypeFactory(title='From')
    _from_new = SavingTypeFactory(title='From-New')

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.get(account_id=_to.pk)
    assert actual.account.title == 'To'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.from_account = _from_new
    obj_update.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=_to.pk)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=_to_new.pk)
    assert actual.account.title == 'To-New'
    assert actual.past == 0.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk)
    assert actual.saving_type.title == 'From-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_close_post_delete():
    obj = SavingCloseFactory()

    SavingClose.objects.get(pk=obj.pk).delete()

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
    SavingClose.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account To'
    assert actual[0]['incomes'] == 1.0
    assert actual[0]['balance'] == 1.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == -1.0

    assert SavingClose.objects.all().count() == 1


def test_saving_close_from_db_classmethod():
    _from = SavingTypeFactory(title='X')
    _to = AccountFactory(title='Y')

    SavingCloseFactory(from_account=_from, to_account=_to)

    obj = SavingClose.objects.last()

    expect = {'account_id': [_to.pk], 'saving_type_id': [_from.pk]}

    assert obj._old_values == expect


def test_saving_close_balance_incomes(savings_close):
    actual = SavingClose.objects.incomes()

    # 1974
    assert actual[0]['year'] == 1970
    assert actual[0]['incomes'] == 0.25
    assert actual[0]['id'] == 1

    # 1999
    assert actual[1]['year'] == 1999
    assert actual[1]['incomes'] == 0.25
    assert actual[1]['id'] == 1

    assert actual[2]['year'] == 1999
    assert actual[2]['incomes'] == 0.0
    assert actual[2]['id'] == 2


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


def test_saving_change_post_save():
    SavingChangeFactory()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == -10.0

    assert actual[1]['title'] == 'Savings To'
    assert actual[1]['invested'] == 10.0
    assert actual[1]['fees'] == 0.0
    assert actual[1]['incomes'] == 10.0


def test_saving_change_post_save_update():
    _to = SavingTypeFactory(title='To')
    _from = SavingTypeFactory(title='From')
    obj = SavingChangeFactory(to_account=_to, from_account=_from)

    # update price
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    actual = SavingBalance.objects.get(pk=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.invested == 0.0
    assert actual.fees == 0.25
    assert actual.incomes == -1.0

    actual = SavingBalance.objects.get(pk=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.invested == 1.0
    assert actual.fees == 0.0
    assert actual.incomes == 1.0


def test_saving_change_post_save_first_record():
    _to = SavingTypeFactory(title='To')
    _from = SavingTypeFactory(title='From')

    SavingFactory(saving_type=_to, price=5, date=date(1998, 1, 1), fee=0.25)
    SavingFactory(saving_type=_from, price=4, date=date(1998, 1, 1), fee=0.25)

    # truncate table
    SavingBalance.objects.all().delete()

    SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 4.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.5
    assert actual.invested == 2.5
    assert actual.incomes == 3.0

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 5.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.25
    assert actual.invested == 5.75
    assert actual.incomes == 6.0


def test_saving_change_post_save_new():
    _to = SavingTypeFactory(title='To')
    _from = SavingTypeFactory(title='From')

    SavingFactory(saving_type=_to, price=5, date=date(1998, 1, 1), fee=0.25)
    SavingFactory(saving_type=_from, price=4, date=date(1998, 1, 1), fee=0.25)

    SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 4.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.5
    assert actual.invested == 2.5
    assert actual.incomes == 3.0

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 5.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.25
    assert actual.invested == 5.75
    assert actual.incomes == 6.0


def test_saving_change_post_save_update_nothing_changed():
    _to = SavingTypeFactory(title='To')
    _from = SavingTypeFactory(title='From')

    SavingFactory(saving_type=_to, price=5, date=date(1998, 1, 1), fee=0.25)
    SavingFactory(saving_type=_from, price=4, date=date(1998, 1, 1), fee=0.25)

    # create saving change
    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    # update saving change
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.save()

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 4.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.5
    assert actual.invested == 2.5
    assert actual.incomes == 3.0

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 5.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.25
    assert actual.invested == 5.75
    assert actual.incomes == 6.0


def test_saving_change_post_save_changed_from():
    _to = SavingTypeFactory(title='To')
    _from = SavingTypeFactory(title='From')
    _from_new = SavingTypeFactory(title='From-New')

    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0

    # update
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.from_account = _from_new
    obj_update.save()

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk)
    assert actual.saving_type.title == 'From-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 1.0
    assert actual.incomes == 1.0


def test_saving_change_post_save_changed_to():
    _to = SavingTypeFactory(title='To')
    _to_new = SavingTypeFactory(title='To-New')
    _from = SavingTypeFactory(title='From')

    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 1.0
    assert actual.incomes == 1.0

    # update
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.save()

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_to_new.pk)
    assert actual.saving_type.title == 'To-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 1.0
    assert actual.incomes == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_change_post_save_changed_to_and_from():
    _to = SavingTypeFactory(title='To')
    _to_new = SavingTypeFactory(title='To-New')
    _from = SavingTypeFactory(title='From')
    _from_new = SavingTypeFactory(title='From-New')

    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 1.0
    assert actual.incomes == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0

    # update
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.from_account = _from_new
    obj_update.save()

    actual = SavingBalance.objects.get(saving_type_id=_to.pk)
    assert actual.saving_type.title == 'To'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_to_new.pk)
    assert actual.saving_type.title == 'To-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 1.0
    assert actual.incomes == 1.0

    actual = SavingBalance.objects.get(saving_type_id=_from.pk)
    assert actual.saving_type.title == 'From'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk)
    assert actual.saving_type.title == 'From-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.0
    assert actual.incomes == -1.0


def test_saving_change_post_delete():
    obj = SavingChangeFactory()

    SavingChange.objects.get(pk=obj.pk).delete()

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

    SavingChange.objects.get(pk=obj.pk).delete()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    assert actual[0]['title'] == 'Savings From'
    assert actual[0]['invested'] == 0.0
    assert actual[0]['fees'] == 0.25
    assert actual[0]['incomes'] == -1.0

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
