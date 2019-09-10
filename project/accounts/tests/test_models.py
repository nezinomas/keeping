from decimal import Decimal

import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..models import Account

pytestmark = pytest.mark.django_db


def test_balance_only_incomes_query(incomes):
    expect = [{
        'title': 'Account1',
        'i_past': 5.25,
        'i_now': 3.25,

    }, {
        'title': 'Account2',
        'i_past': 4.5,
        'i_now': 3.5,
    }]

    actual = list(Account.objects.incomes(1999).values())

    assert_(expect, actual)


def test_incomes_only(incomes):
    expect = [{
        'title': 'Account1',
        'past': Decimal(5.25),
        'incomes': Decimal(3.25),
        'expenses': Decimal(0.0),
        'balance': Decimal(8.5),
    }, {
        'title': 'Account2',
        'past': Decimal(4.50),
        'incomes': Decimal(3.5),
        'expenses': Decimal(0.0),
        'balance': Decimal(8.0),
    }]

    actual = list(Account.objects.balance_year(1999))

    assert_(expect, actual)


def test_balance_only_expenses_query(expenses):
    expect = [{
        'title': 'Account1',
        'e_past': 2.5,
        'e_now': 0.5,

    }, {
        'title': 'Account2',
        'e_past': 2.25,
        'e_now': 1.25,
    }]

    actual = list(Account.objects.expenses(1999).values())

    assert_(expect, actual)


def test_balance_only_expenses(expenses):
    expect = [{
        'title': 'Account1',
        'past': -2.50,
        'incomes': 0.0,
        'expenses': 0.50,
        'balance': -3.00,
    }, {
        'title': 'Account2',
        'past': -2.25,
        'incomes': 0.0,
        'expenses': 1.25,
        'balance': -3.5,
    }]

    actual = list(Account.objects.balance_year(1999))

    assert_(expect, actual)


def test_balance_only_transactions_balance_year(transactions):
    expect = [{
        'title': 'Account1',
        'past': 4.0,
        'incomes': 3.25,
        'expenses': 4.5,
        'balance': 2.75,
    }, {
        'title': 'Account2',
        'past': -4.0,
        'incomes': 4.5,
        'expenses': 3.25,
        'balance': -2.75,
    }]

    actual = list(Account.objects.balance_year(1999))

    assert_(expect, actual)


def test_balance_only_transactions_from_query(transactions):
    expect = [{
        'title': 'Account1',
        'tr_from_past': 1.25,
        'tr_from_now': 4.5,
    }, {
        'title': 'Account2',
        'tr_from_past': 5.25,
        'tr_from_now': 3.25,
    }]

    actual = list(Account.objects.all().transactions_from(1999).values())

    assert_(expect, actual)


def test_balance_only_transactions_to_query(transactions):
    expect = [{
        'title': 'Account1',
        'tr_to_past': 5.25,
        'tr_to_now': 3.25,
    }, {
        'title': 'Account2',
        'tr_to_past': 1.25,
        'tr_to_now': 4.5,
    }]

    actual = list(Account.objects.all().transactions_to(1999).values())

    assert_(expect, actual)


def test_balance_only_savings_query(savings):
    expect = [{
        'title': 'Account1',
        's_past': 1.25,
        's_now': 3.5,

    }, {
        'title': 'Account2',
        's_past': 0.25,
        's_now': 2.25,
    }]

    actual = list(Account.objects.savings(1999).values())

    assert_(expect, actual)


def test_balance_only_savings_balance_year(savings):
    expect = [{
        'title': 'Account1',
        'past': -1.25,
        'incomes': 0.0,
        'expenses': 3.50,
        'balance': -4.75,
    }, {
        'title': 'Account2',
        'past': -0.25,
        'incomes': 0.0,
        'expenses': 2.25,
        'balance': -2.50,
    }]

    actual = list(Account.objects.all().balance_year(1999))

    assert_(expect, actual)


def test_balance_only_savings_close_balance_year(savings_close):
    expect = [{
        'title': 'Account1',
        'past': 0.25,
        'incomes': 0.25,
        'expenses': 0.0,
        'balance': 0.5,
    }, {
        'title': 'Account2',
        'past': 0.0,
        'incomes': 0.0,
        'expenses': 0.0,
        'balance': 0.0,
    }]

    actual = list(Account.objects.balance_year(1999))

    assert_(expect, actual)


def test_balance(incomes, expenses, savings, transactions, savings_close):
    expect = [{
        'title': 'Account1',
        'past': 5.75,
        'incomes': 6.75,
        'expenses': 8.5,
        'balance': 4.0,
    }, {
        'title': 'Account2',
        'past': -2.0,
        'incomes': 8.0,
        'expenses': 6.75,
        'balance': -0.75,
    }]

    actual = list(Account.objects.balance_year(1999))

    assert_(expect, actual)


def test_balance_past(incomes, expenses, savings, transactions, savings_close):
    expect = [{
        'title': 'Account1',
        'past': 0.0,
        'incomes': 10.75,
        'expenses': 5.0,
        'balance': 5.75,
    }, {
        'title': 'Account2',
        'past': 0.0,
        'incomes': 5.75,
        'expenses': 7.75,
        'balance': -2.0,
    }]

    actual = list(Account.objects.balance_year(1970))

    assert_(expect, actual)


# Still dont know how to implement in one query
#
# def test_accounts_worth(accounts_worth):
#     expect = [{
#         'title': 'Account1',
#         'have': 3.25,
#     }, {
#         'title': 'Account2',
#         'have': 8.0,
#     }]
#     actual = list(Account.objects.balance_year(1970))

#     assert_(expect, actual)
