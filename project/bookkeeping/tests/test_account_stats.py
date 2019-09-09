import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..lib.account_stats import AccountStats as T


@pytest.fixture()
def _accounts():
    return (
        [{
            'account': 'Account1',
            'past': 10.0,
            'incomes': 20.0,
            'expenses': 25.0,
            'balance': 5.75,
        }, {
            'account': 'Account2',
            'past': 5.0,
            'incomes': 5.0,
            'expenses': 5.0,
            'balance': 2.0,
        }]
    )


@pytest.fixture()
def _accounts_worth():
    return ([
        {'account': 'Account1', 'have': 5.75},
        {'account': 'Account2', 'have': 1.0},
    ])


@pytest.mark.xfail(raises=Exception)
def test_empty_accounts_stats():
    actual = T([], None).balance


@pytest.mark.xfail(raises=Exception)
def test_none_accounts_stats():
    actual = T(None, None).balance


def test_account_stats(_accounts, _accounts_worth):
    expect = [{
        'account': 'Account1',
        'balance': 5.75,
        'have': 5.75,
        'delta': 0.0
    }, {
        'account': 'Account2',
        'balance': 2.0,
        'have': 1.0,
        'delta': -1.0
    }]

    actual = T(_accounts, _accounts_worth).balance

    assert_(expect, actual)


def test_account_stats_worth_empty(_accounts):
    expect = [{
        'account': 'Account1',
        'balance': 5.75,
        'have': 0.0,
        'delta': -5.75
    }, {
        'account': 'Account2',
        'balance': 2.0,
        'have': 0.0,
        'delta': -2.0
    }]

    actual = T(_accounts, []).balance

    assert_(expect, actual)


def test_account_stats_worth_None(_accounts):
    expect = [{
        'account': 'Account1',
        'balance': 5.75,
        'have': 0.0,
        'delta': -5.75
    }, {
        'account': 'Account2',
        'balance': 2.0,
        'have': 0.0,
        'delta': -2.0
    }]

    actual = T(_accounts, None).balance

    assert_(expect, actual)


def test_account_totals(_accounts, _accounts_worth):
    expect = {
        'past': 15.0,
        'incomes': 25.0,
        'expenses': 30.0,
        'balance': 7.75,
        'have': 6.75,
        'delta': -1.0
    }

    actual = T(_accounts, _accounts_worth).totals

    assert expect == actual
