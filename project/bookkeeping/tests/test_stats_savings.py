import pytest

from ..lib.stats_savings import StatsSavings


def round_(_list):
    for key, arr in _list.items():
        for _k, _v in _list[key].items():
            _list[key][_k] = round(_v, 2)


def test_savings_year_now(_data_savings):
    expect = {
        'Saving1': {
            'past_amount': -1.25,
            'past_fee': 0.40,
            'incomes': 0.75,
            'fees': 0.95,
            'invested': -0.20,
        },
        'Saving2': {
            'past_amount': 2.50,
            'past_fee': 0.15,
            'incomes': 6.00,
            'fees': 0.45,
            'invested': 5.55,
        },
    }

    actual = StatsSavings(1999, _data_savings).balance
    round_(actual)

    assert expect == actual


def test_savings_year_past(_data_savings):
    actual = StatsSavings(1970, _data_savings).balance

    expect = {
        'Saving1': {
            'past_amount': 0.00,
            'past_fee': 0.0,
            'incomes': -1.25,
            'fees': 0.40,
            'invested': -1.65,
        },
        'Saving2': {
            'past_amount': 0.00,
            'past_fee': 0.00,
            'incomes': 2.50,
            'fees': 0.15,
            'invested': 2.35,
        },
    }

    assert expect == actual


def test_savings_change_only(_savings_change):
    actual = StatsSavings(1999, _savings_change).balance

    expect = {
        'Saving1': {
            'past_amount': -2.25,
            'past_fee': 0.15,
            'incomes': -3.50,
            'fees': 0.20,
            'invested': -3.70,
        },
        'Saving2': {
            'past_amount': 2.25,
            'past_fee': 0.15,
            'incomes': 3.50,
            'fees': 0.20,
            'invested': 3.30,
        },
    }

    assert expect == actual


def test_savings_empty():
    actual = StatsSavings(1, {}).balance

    assert actual.empty
