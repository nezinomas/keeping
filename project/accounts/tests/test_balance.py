from decimal import Decimal

import pandas as pd
import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..lib.balance import Balance as T


@pytest.fixture()
def _accounts():
    df = pd.DataFrame([{
        'id': 1,
        'title': 'Account1',
        'i_past': 5.25, 'i_now': 3.25,
        'e_past': 2.5, 'e_now': 0.5,
        's_past': 1.25, 's_now': 3.5,
        'tr_from_past': 1.25, 'tr_from_now': 4.5,
        'tr_to_past': 5.25, 'tr_to_now': 3.25,
        's_close_to_past': 0.25, 's_close_to_now': 0.25,
        'borrow_past': 0, 'borrow_now': 0,
        'borrow_return_past': 0, 'borrow_return_now': 0,
        'lent_past': 0, 'lent_now': 0,
        'lent_return_past': 0, 'lent_return_now': 0,
    }, {
        'id': 2,
        'title': 'Account2',
        'i_past': 4.5, 'i_now': 3.5,
        'e_past': 2.25, 'e_now': 1.25,
        's_past': 0.25, 's_now': 2.25,
        'tr_from_past': 5.25, 'tr_from_now': 3.25,
        'tr_to_past': 1.25, 'tr_to_now': 4.5,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        'borrow_past': 0, 'borrow_now': 0,
        'borrow_return_past': 0, 'borrow_return_now': 0,
        'lent_past': 0, 'lent_now': 0,
        'lent_return_past': 0, 'lent_return_now': 0,
    }])

    df.set_index('title', inplace=True)
    return df


@pytest.fixture()
def _accounts_worth():
    return ([
        {'title': 'Account1', 'have': Decimal(5.75)},
        {'title': 'Account2', 'have': Decimal(1.0)},
    ])


def test_empty_accounts_stats():
    actual = T([], None).balance

    assert actual == []


def test_none_accounts_stats():
    actual = T(None, None).balance

    assert actual == []


def test_empty_data_ef_for_accounts_stats():
    actual = T(pd.DataFrame(), None).balance

    assert actual == []


def test_account_stats(_accounts, _accounts_worth):
    expect = [{
        'id': 1,
        'title': 'Account1',
        'past': 5.75,
        'incomes': 6.75,
        'expenses': 8.5,
        'balance': 4.0,
        'have': 5.75,
        'delta': 1.75
    }, {
        'id': 2,
        'title': 'Account2',
        'past': -2.0,
        'incomes': 8.0,
        'expenses': 6.75,
        'balance': -0.75,
        'have': 1.0,
        'delta': 1.75
    }]

    actual = T(_accounts, _accounts_worth).balance

    assert_(expect, actual)


def test_account_stats_worth_empty(_accounts):
    expect = [{
        'id': 1,
        'title': 'Account1',
        'past': 5.75,
        'incomes': 6.75,
        'expenses': 8.5,
        'balance': 4.0,
        'have': 0.0,
        'delta': -4.0
    }, {
        'id': 2,
        'title': 'Account2',
        'past': -2.0,
        'incomes': 8.0,
        'expenses': 6.75,
        'balance': -0.75,
        'have': 0.0,
        'delta': 0.75
    }]

    actual = T(_accounts, []).balance

    assert_(expect, actual)


@pytest.mark.parametrize(
    'worth',
    [
        {'title': 'Account1', 'have': 0},
        {'title': 'Account1', 'have': 'x'},
        {'title': 'Account1', 'have': ''},
        {'title': 'Account1', 'have1': 'x'},
    ]
)
def test_account_stats_worth_with_invalid_data(worth, _accounts):
    expect = [{
        'id': 1,
        'title': 'Account1',
        'past': 5.75,
        'incomes': 6.75,
        'expenses': 8.5,
        'balance': 4.0,
        'have': 0.0,
        'delta': -4.0
    }, {
        'id': 2,
        'title': 'Account2',
        'past': -2.0,
        'incomes': 8.0,
        'expenses': 6.75,
        'balance': -0.75,
        'have': 0.0,
        'delta': 0.75
    }]

    actual = T(
        _accounts, [worth]).balance

    assert_(expect, actual)


def test_account_stats_worth_None(_accounts):
    expect = [{
        'id': 1,
        'title': 'Account1',
        'past': 5.75,
        'incomes': 6.75,
        'expenses': 8.5,
        'balance': 4.0,
        'have': 0.0,
        'delta': -4.0,
    }, {
        'id': 2,
        'title': 'Account2',
        'past': -2.0,
        'incomes': 8.0,
        'expenses': 6.75,
        'balance': -0.75,
        'have': 0.0,
        'delta': 0.75
    }]

    actual = T(_accounts, None).balance

    assert_(expect, actual)


def test_account_total_row(_accounts, _accounts_worth):
    expect = {
        'past': 3.75,
        'incomes': 14.75,
        'expenses': 15.25,
        'balance': 3.25,
        'have': 6.75,
        'delta': 3.5
    }

    actual = T(_accounts, _accounts_worth).total_row

    for k, v in expect.items():
        assert v == actual[k]


def test_account_past_property(_accounts):
    expect = 3.75

    actual = T(_accounts, None).balance_start

    assert expect == actual


def test_account_past_property_no_accounts():
    expect = 0.0

    actual = T(None, None).balance_start

    assert expect == actual


def test_balance_end(_accounts):
    expect = 3.25

    actual = T(_accounts, []).balance_end

    assert expect == actual