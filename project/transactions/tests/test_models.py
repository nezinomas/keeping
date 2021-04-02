from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...savings.factories import SavingTypeFactory
from ...savings.models import SavingBalance
from ..factories import (SavingChangeFactory, SavingCloseFactory,
                         TransactionFactory)
from ..models import SavingChange, SavingClose, Transaction
from ...users.factories import UserFactory

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_str():
    t = TransactionFactory.build()

    assert str(t) == '1999-01-01 Account1->Account2: 200'


def test_transaction_related():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')

    t1 = AccountFactory(title='T1', user=u1)
    f1 = AccountFactory(title='F1', user=u1)

    t2 = AccountFactory(title='T2', user=u2)
    f2 = AccountFactory(title='F2', user=u2)

    TransactionFactory(to_account=t1, from_account=f1)
    TransactionFactory(to_account=t2, from_account=f2)

    actual = Transaction.objects.related()

    assert len(actual) == 1
    assert str(actual[0].from_account) == 'F1'
    assert str(actual[0].to_account) == 'T1'


def test_transaction_items():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')

    t1 = AccountFactory(title='T1', user=u1)
    f1 = AccountFactory(title='F1', user=u1)

    t2 = AccountFactory(title='T2', user=u2)
    f2 = AccountFactory(title='F2', user=u2)

    TransactionFactory(to_account=t1, from_account=f1)
    TransactionFactory(to_account=t2, from_account=f2)

    actual = Transaction.objects.related()

    assert len(actual) == 1
    assert str(actual[0].from_account) == 'F1'
    assert str(actual[0].to_account) == 'T1'


def test_transaction_year():
    a = AccountFactory(title='T1', user=UserFactory(username='XXX'))

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


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_str():
    s = SavingCloseFactory.build()

    assert str(s) == '1999-01-01 Savings From->Account To: 10'


def test_saving_close_related():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')

    a1 = AccountFactory(title='A1', user=u1)
    a2 = AccountFactory(title='A2', user=u2)

    s1 = SavingTypeFactory(title='S1', user=u1)
    s2 = SavingTypeFactory(title='S2', user=u2)

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
        's_close_from_past': 0.25,
        's_close_from_now': 0.25,
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


def test_saving_close_post_save_saving_balance():
    account = AccountFactory()
    saving = SavingTypeFactory()

    obj = SavingClose(
        date=date(1999, 1, 1),
        price=Decimal(1),
        fee=Decimal(0.5),
        from_account=saving,
        to_account=account
    )

    obj.save()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Savings'
    assert actual['past_amount'] == 0.0
    assert actual['past_fee'] == 0.0
    assert actual['incomes'] == -1.0
    assert actual['fees'] == 0.0
    assert actual['invested'] == -1.0


# ----------------------------------------------------------------------------
#                                                                 Saving Change
# ----------------------------------------------------------------------------
def test_savings_change_str():
    s = SavingChangeFactory.build()

    assert str(s) == '1999-01-01 Savings From->Savings To: 10'


def test_saving_change_related():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')

    f1 = SavingTypeFactory(title='F1', user=u1)
    f2 = SavingTypeFactory(title='F2', user=u2)

    t1 = SavingTypeFactory(title='T1', user=u1)
    t2 = SavingTypeFactory(title='T2', user=u2)

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


def test_saving_change_post_save_saving_balance():
    _from = SavingTypeFactory(title='F')
    _to = SavingTypeFactory(title='T')

    obj = SavingChange(
        date=date(1999, 1, 1),
        price=Decimal(1),
        fee=Decimal(0.5),
        to_account=_to,
        from_account=_from,
    )

    obj.save()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    actual = actual[0]

    assert actual['title'] == 'F'
    assert actual['past_amount'] == 0.0
    assert actual['past_fee'] == 0.0
    assert actual['incomes'] == -1.0
    assert actual['fees'] == 0.5
    assert actual['invested'] == -1.5
