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

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transactions_str():
    t = TransactionFactory.build()

    assert str(t) == '1999-01-01 Account1->Account2: 200'


def test_transactions_year():
    TransactionFactory(date=date(1999, 1, 1))
    TransactionFactory(date=date(2000, 1, 1))

    actual = Transaction.objects.year(1999)

    assert actual.count() == 1


def test_transactions_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(Transaction.objects.items())


def test_transactions_year_query_count(django_assert_max_num_queries):
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
def test_savings_close_str():
    s = SavingCloseFactory.build()

    assert str(s) == '1999-01-01 Savings From->Account To: 10'


def test_saving_close_month_sums(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.month_sum(1999))

    assert expect == actual


def test_saving_close_month_sums_only_january(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.month_sum(1999, 1))

    assert expect == actual


def test_saving_close_month_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(SavingClose.objects.month_sum(1999))


def test_savings_close_summary_from(savings_close):
    expect = [{
        'title': 'Saving1',
        's_close_from_past': 0.25,
        's_close_from_now': 0.25,
    }]

    actual = list(
        SavingClose.objects
        .summary_from(1999).order_by('from_account__title'))

    assert expect == actual


def test_savings_close_summary_to(savings_close):
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


def test_saving_close_post_save_saving_balance(get_user):
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

    actual = SavingBalance.objects.items(1999)

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


def test_saving_change_post_save_saving_balance(get_user):
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

    actual = SavingBalance.objects.items(1999)

    assert actual.count() == 2

    actual = actual[0]

    assert actual['title'] == 'F'
    assert actual['past_amount'] == 0.0
    assert actual['past_fee'] == 0.0
    assert actual['incomes'] == -1.0
    assert actual['fees'] == 0.5
    assert actual['invested'] == -1.5
