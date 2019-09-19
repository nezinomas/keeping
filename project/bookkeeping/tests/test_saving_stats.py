import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..lib.saving_stats import SavingStats as T


@pytest.fixture()
def _savings():
    return (
        [{
            'title': 'Saving1',
            'incomes': 4.75,
            'invested': 4.0,
        }, {
            'title': 'Saving2',
            'incomes': 2.50,
            'invested': 2.25,
        }]
    )


@pytest.fixture()
def _savings_worth():
    return (
        [{
            'title': 'Saving1',
            'have': 0.15,
        }, {
            'title': 'Saving2',
            'have': 6.15,
        }]
    )


@pytest.fixture()
def _pension():
    return (
        [{
            'title': 'Saving',
            'incomes': 1.0,
            'invested': 1.0,
        }, {
            'title': 'Pension',
            'incomes': 2.0,
            'invested': 2.0,
        }]
    )


def test_empty_savings_stats():
    actual = T([], None).balance

    assert actual is None


def test_none_savings_stats():
    actual = T(None, None).balance

    assert actual is None


def test_savings_worth(_savings, _savings_worth):
    expect = [{
        'title': 'Saving1',
        'incomes': 4.75,
        'invested': 4.0,
        'market_value': 0.15,
        'profit_incomes_proc': -96.84,
        'profit_incomes_sum': -4.6,
        'profit_invested_proc': -96.25,
        'profit_invested_sum': -3.85,
    }, {
        'title': 'Saving2',
        'incomes': 2.50,
        'invested': 2.25,
        'market_value': 6.15,
        'profit_incomes_proc': 146.0,
        'profit_incomes_sum': 3.65,
        'profit_invested_proc': 173.33,
        'profit_invested_sum': 3.9,
    }]

    actual = T(_savings, _savings_worth).balance

    assert_(expect, actual)


def test_saving_stats_worth_empty(_savings):
    expect = [{
        'title': 'Saving1',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'title': 'Saving2',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]

    actual = T(_savings, []).balance

    assert_(expect, actual)


def test_saving_stats_worth_None(_savings):
    expect = [{
        'title': 'Saving1',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'title': 'Saving2',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]

    actual = T(_savings, None).balance

    assert_(expect, actual)


def test_saving_totals(_savings, _savings_worth):
    expect = {
        'incomes': 7.25,
        'invested': 6.25,
        'market_value': 6.3,
        'profit_incomes_proc': -13.10,
        'profit_incomes_sum': -0.95,
        'profit_invested_proc': 0.8,
        'profit_invested_sum': 0.05,
    }

    actual = T(_savings, _savings_worth).totals

    assert expect == pytest.approx(actual, rel=1e-3)


def test_savings_only(_pension):
    actual = T(_pension, None, saving_type='fund').balance

    assert 1 == len(actual)
    assert 'Saving' == actual[0]['title']


def test_pension_only(_pension):
    actual = T(_pension, None, saving_type='pension').balance

    assert 1 == len(actual)
    assert 'Pension' == actual[0]['title']


def test_savings_all(_pension):
    actual = T(_pension, None).balance

    assert 2 == len(actual)
    assert 'Saving' == actual[0]['title']
    assert 'Pension' == actual[1]['title']
