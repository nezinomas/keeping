import pytest

from ..lib.stats_savings import StatsSavings


def test_savings_year_now(_data_savings):
    actual = StatsSavings(1999, _data_savings).balance

    expect = {
        'Saving1': {
            'past_amount': 1000.0,
            'past_fee': 145.68,
            'incomes': 500.0,
            'fees': 30.5,
            'invested': 469.5,
        },
        'Saving2': {
            'past_amount': 100.0,
            'past_fee': 15.5,
            'incomes': 300.0,
            'fees': 15.5,
            'invested': 284.5,
        },
    }

    assert expect == actual


def test_savings_year_past(_data_savings):
    actual = StatsSavings(1970, _data_savings).balance

    expect = {
        'Saving1': {
            'past_amount': .0,
            'past_fee': 0.0,
            'incomes': 1000.0,
            'fees': 145.68,
            'invested': 854.32,
        },
        'Saving2': {
            'past_amount': 0.0,
            'past_fee': 0.0,
            'incomes': 100.0,
            'fees': 15.5,
            'invested': 84.5,
        },
    }

    assert expect['Saving1'] == pytest.approx(actual['Saving1'])
    assert expect['Saving2'] == pytest.approx(actual['Saving2'])
