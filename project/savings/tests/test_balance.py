from decimal import Decimal

import pandas as pd
import pytest

from ...core.tests.utils import equal_list_of_dictionaries as my_assert
from ..lib.balance import Balance as T


def _make_df(arr):
    d = {
        'id': 1,
        'title': 'x',
        's_past': 0.0,
        's_now': 0.0,
        's_fee_past': 0.0,
        's_fee_now': 0.0,
        's_close_to_past': 0.0,
        's_close_to_now': 0.0,
        's_close_from_past': 0.0,
        's_close_from_now': 0.0,
        's_close_from_fee_past': 0.0,
        's_close_from_fee_now': 0.0,
        's_change_to_past': 0.0,
        's_change_to_now': 0.0,
        's_change_from_past': 0.0,
        's_change_from_now': 0.0,
        's_change_from_fee_past': 0.0,
        's_change_from_fee_now': 0.0,
    }

    for k, v in arr.items():
        d[k] = v

    df = pd.DataFrame([d])
    df.set_index('title', inplace=True)

    return df


@pytest.fixture()
def _savings():
    df = pd.DataFrame([{
        'id': 1,
        'title': 'Saving1',
        's_past': 1.25, 's_now': 3.5,
        's_fee_past': 0.25, 's_fee_now': 0.5,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        's_close_from_past': 0.25, 's_close_from_now': 0.25,
        's_close_from_fee_past': 0.0, 's_close_from_fee_now': 0.0,
        's_change_to_past': 0.0, 's_change_to_now': 0.0,
        's_change_from_past': 2.25, 's_change_from_now': 1.25,
        's_change_from_fee_past': 0.15, 's_change_from_fee_now': 0.05
    }, {
        'id': 2,
        'title': 'Saving2',
        's_past': 0.25, 's_now': 2.25,
        's_fee_past': 0.0, 's_fee_now': 0.25,
        's_close_to_past': 0.0, 's_close_to_now': 0.0,
        's_close_from_past': 0.0, 's_close_from_now': 0.0,
        's_close_from_fee_past': 0.0, 's_close_from_fee_now': 0.0,
        's_change_to_past': 2.25, 's_change_to_now': 1.25,
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


def test_empty_savings_stats():
    actual = T([], None).balance

    assert actual == []


def test_empty_data_frame_savings_stats():
    actual = T(pd.DataFrame(), None).balance

    assert actual == []


def test_none_savings_stats():
    actual = T(None, None).balance

    assert actual == []


def test_none_savings_stats_total_row():
    actual = T([], None).total_row

    assert actual == {}


def test_saving_only(_savings):
    expect = [{
        'id': 1,
        'title': 'Saving1',
        'past_amount': -1.25,
        'past_fee': 0.4,
        'incomes': 2.25,
        'fees': 0.95,
        'invested': 0.0,
        'market_value': 0.0,
    }, {
        'id': 2,
        'title': 'Saving2',
        'past_amount': 2.5,
        'past_fee': 0.0,
        'incomes': 6.0,
        'fees': 0.25,
        'invested': 5.75,
        'market_value': 0.0,
    }]

    actual = T(_savings, []).balance

    my_assert(expect, actual)


def test_saving_when_worth_filled_partially(_savings):
    expect = [{
        'id': 1,
        'title': 'Saving1',
        'past_amount': -1.25,
        'past_fee': 0.4,
        'incomes': 2.25,
        'fees': 0.95,
        'invested': 0.0,
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'id': 2,
        'title': 'Saving2',
        'past_amount': 2.5,
        'past_fee': 0.0,
        'incomes': 6.0,
        'fees': 0.25,
        'invested': 5.75,
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]
    worth = [{'title': 'Saving1', 'have': Decimal(0)}]

    actual = T(_savings, worth).balance

    my_assert(expect, actual)


def test_savings_worth(_savings, _savings_worth):
    expect = [{
        'id': 1,
        'title': 'Saving1',
        'incomes': 2.25,
        'invested': 0.0,
        'market_value': 0.15,
        'profit_incomes_proc': -93.33,
        'profit_incomes_sum': -2.1,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.15,
    }, {
        'id': 2,
        'title': 'Saving2',
        'incomes': 6.0,
        'invested': 5.75,
        'market_value': 6.15,
        'profit_incomes_proc': 2.5,
        'profit_incomes_sum': 0.15,
        'profit_invested_proc': 6.96,
        'profit_invested_sum': 0.4,
    }]

    actual = T(_savings, _savings_worth).balance

    my_assert(expect, actual)


def test_saving_stats_worth_empty(_savings):
    expect = [{
        'id': 1,
        'title': 'Saving1',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'id': 2,
        'title': 'Saving2',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]

    actual = T(_savings, []).balance

    my_assert(expect, actual)


@pytest.mark.parametrize(
    'worth',
    [
        {'title': 'Saving1', 'have': 0},
        {'title': 'Saving1', 'have': 'x'},
        {'title': 'Saving1', 'have': ''},
        {'title': 'Saving1', 'haveX': 'x'},
    ]
)
def test_saving_stats_worth_invalid_have(worth, _savings):
    expect = [{
        'id': 1,
        'title': 'Saving1',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'id': 2,
        'title': 'Saving2',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]

    actual = T(_savings, [worth]).balance

    my_assert(expect, actual)


def test_saving_stats_worth_None(_savings):
    expect = [{
        'id': 1,
        'title': 'Saving1',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }, {
        'id': 2,
        'title': 'Saving2',
        'market_value': 0.0,
        'profit_incomes_proc': 0.0,
        'profit_incomes_sum': 0.0,
        'profit_invested_proc': 0.0,
        'profit_invested_sum': 0.0,
    }]

    actual = T(_savings, None).balance

    my_assert(expect, actual)


def test_saving_total_row(_savings, _savings_worth):
    expect = {
        'past_amount': 1.25,
        'past_fee': 0.4,
        'incomes': 8.25,
        'fees': 1.2,
        'invested': 5.75,
        'market_value': 6.3,
        'profit_incomes_proc': -23.64,
        'profit_incomes_sum': -1.95,
        'profit_invested_proc': 9.56,
        'profit_invested_sum': 0.55,
    }

    actual = T(_savings, _savings_worth).total_row

    for k, v in expect.items():
        assert v == pytest.approx(actual[k], rel=1e-2)


def test_savings_total_market(_savings, _savings_worth):
    actual = T(_savings, _savings_worth).total_market

    assert pytest.approx(actual, rel=1e-2) == 6.3


def test_savings_total_market_empty_lists():
    actual = T([], []).total_market

    assert actual == 0


def test_savings_total_market_none_values():
    actual = T(None, None).total_market

    assert actual == 0


def test_close_saving_no_profit():
    arr = {
        's_now': 15,
        's_fee_now': 2,
        's_close_from_now': 5,
        's_close_from_fee_now': 40,
    }

    actual = T(_make_df(arr), None).balance[0]

    assert actual['incomes'] == 15.0
    assert actual['fees'] == 42.0
    assert actual['invested'] == 0.0


def test_close_saving_with_profit():
    arr = {
        's_now': 15,
        's_fee_now': 2,
        's_close_from_now': 32,
    }

    actual = T(_make_df(arr), None).balance[0]

    assert actual['incomes'] == 15.0
    assert actual['fees'] == 2.0
    assert actual['invested'] == 0.0