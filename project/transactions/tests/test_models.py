from datetime import date
from decimal import Decimal

import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..factories import (SavingChangeFactory, SavingCloseFactory,
                         TransactionFactory)
from ..models import SavingChange, SavingClose, Transaction


@pytest.mark.django_db
def test_month_sums(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.month_sum(1999))

    assert expect == actual


@pytest.mark.django_db
def test_month_sums_only_january(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.month_sum(1999, 1))

    assert expect == actual


def test_transactions_str():
    t = TransactionFactory.build()

    assert '1999-01-01 Account1->Account2: 200' == str(t)


def test_savings_close_str():
    s = SavingCloseFactory.build()

    assert '1999-01-01 Savings From->Account To: 10' == str(s)


def test_savings_change_str():
    s = SavingChangeFactory.build()

    assert '1999-01-01 Savings From->Savings To: 10' == str(s)


@pytest.mark.django_db
def test_transactions_year():
    TransactionFactory(date=date(1999, 1, 1))
    TransactionFactory(date=date(2000, 1, 1))

    actual = Transaction.objects.year(1999)

    assert 1 == actual.count()


@pytest.mark.django_db
def test_transactions_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Transaction.objects.items()]


@pytest.mark.django_db
def test_transactions_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Transaction.objects.year(1999)]


@pytest.mark.django_db
def test_saving_close_month_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*SavingClose.objects.month_sum(1999)]


@pytest.mark.django_db
def test_saving_change_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*SavingChange.objects.items()]


@pytest.mark.django_db
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
        .summary_from(1999).order_by('from_account__title'))

    assert expect == actual


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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
        .summary_to(1999).order_by('to_account__title'))

    assert expect == actual


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_savings_change_summary_to(savings_change):
    expect = [{
        's_change_to_past': Decimal(2.25),
        's_change_to_now': Decimal(1.25),
        's_change_to_fee_past': Decimal(0.15),
        's_change_to_fee_now': Decimal(0.05),
    }]

    actual = list(
        SavingChange.objects
        .summary_to(1999).order_by('to_account__title'))

    assert_(expect, actual)
