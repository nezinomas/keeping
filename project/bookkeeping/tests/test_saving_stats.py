import pandas as pd
import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..lib.saving_stats import SavingStats as T


@pytest.fixture()
def _savings():
    df = pd.DataFrame([{
        'title': 'Saving1',
        's_past': 1.25, 's_now': 3.5,
        's_fee_past': 0.25, 's_fee_now': 0.5,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        's_close_from_past': 0.25, 's_close_from_now': 0.25,
        's_change_to_past': 0.0, 's_change_to_now': 0.0,
        's_change_to_fee_past': 0.0, 's_change_to_fee_now': 0.0,
        's_change_from_past': 2.25, 's_change_from_now': 1.25,
        's_change_from_fee_past': 0.15, 's_change_from_fee_now': 0.05
    }, {
        'title': 'Saving2',
        's_past': 0.25, 's_now': 2.25,
        's_fee_past': 0.0, 's_fee_now': 0.25,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        's_close_from_past': 0.0, 's_close_from_now': 0.0,
        's_change_to_past': 2.25, 's_change_to_now': 1.25,
        's_change_to_fee_past': 0.15, 's_change_to_fee_now': 0.05,
        's_change_from_past': 0.0, 's_change_from_now': 0.0,
        's_change_from_fee_past': 0.0, 's_change_from_fee_now': 0.0
    }])

    df.set_index('title', inplace=True)
    return df


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


@pytest.fixture
def _pension():
    df = pd.DataFrame([{
        'title': 'Saving',
        's_past': 1.25, 's_now': 3.5,
        's_fee_past': 0.25, 's_fee_now': 0.5,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        's_close_from_past': 0.25, 's_close_from_now': 0.25,
        's_change_to_past': 0.0, 's_change_to_now': 0.0,
        's_change_to_fee_past': 0.0, 's_change_to_fee_now': 0.0,
        's_change_from_past': 2.25, 's_change_from_now': 1.25,
        's_change_from_fee_past': 0.15, 's_change_from_fee_now': 0.05
    }, {
        'title': 'Pensija3',
        's_past': 0.25, 's_now': 2.25,
        's_fee_past': 0.0, 's_fee_now': 0.25,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        's_close_from_past': 0.0, 's_close_from_now': 0.0,
        's_change_to_past': 2.25, 's_change_to_now': 1.25,
        's_change_to_fee_past': 0.15, 's_change_to_fee_now': 0.05,
        's_change_from_past': 0.0, 's_change_from_now': 0.0,
        's_change_from_fee_past': 0.0, 's_change_from_fee_now': 0.0
    }])
    df.set_index('title', inplace=True)
    return df


def test_empty_savings_stats():
    actual = T([], None).balance

    assert actual == []


def test_empty_data_frame_savings_stats():
    actual = T(pd.DataFrame(), None).balance

    assert actual == []


def test_none_savings_stats():
    actual = T(None, None).balance

    assert actual == []


def test_none_savings_stats_totals():
    actual = T([], None).totals

    assert actual == {}


def test_saving_only(_savings):
    expect = [{
        'title': 'Saving1',
        'past_amount': -1.25,
        'past_fee': 0.4,
        'incomes': 0.75,
        'fees': 0.95,
        'invested': -0.2,
    }, {
        'title': 'Saving2',
        'past_amount': 2.5,
        'past_fee': 0.15,
        'incomes': 6.0,
        'fees': 0.45,
        'invested': 5.55,
    }]

    actual = T(_savings, []).balance

    assert_(expect, actual)


def test_savings_worth(_savings, _savings_worth):
    expect = [{
        'title': 'Saving1',
        'incomes': 0.75,
        'invested': -0.2,
        'market_value': 0.15,
        'profit_incomes_proc': -80.0,
        'profit_incomes_sum': -0.6,
        'profit_invested_proc': -175.0,
        'profit_invested_sum': 0.35,
    }, {
        'title': 'Saving2',
        'incomes': 6.0,
        'invested': 5.55,
        'market_value': 6.15,
        'profit_incomes_proc': 2.5,
        'profit_incomes_sum': 0.15,
        'profit_invested_proc': 10.81,
        'profit_invested_sum': 0.6,
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
        'past_amount': 1.25,
        'past_fee': 0.55,
        'incomes': 6.75,
        'fees': 1.4,
        'invested': 5.35,
        'market_value': 6.3,
        'profit_incomes_proc': -6.66,
        'profit_incomes_sum': -0.45,
        'profit_invested_proc': 17.76,
        'profit_invested_sum': 0.95,
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
    assert 'Pensija3' == actual[0]['title']


def test_savings_all(_pension):
    actual = T(_pension, None).balance

    assert 2 == len(actual)
    assert 'Saving' == actual[0]['title']
    assert 'Pensija3' == actual[1]['title']


def test_savings_total_market(_savings, _savings_worth):
    actual = T(_savings, _savings_worth).total_market

    assert 6.3 == pytest.approx(actual, rel=1e-2)


def test_savings_total_market_empty_lists():
    actual = T([], []).total_market

    assert 0 == actual


def test_savings_total_market_none_values():
    actual = T(None, None).total_market

    assert 0 == actual
