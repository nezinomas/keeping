from datetime import date
from decimal import Decimal

import pytest

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
