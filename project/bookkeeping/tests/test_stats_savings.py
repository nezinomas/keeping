import pytest

from ..lib.stats_savings import StatsSavings


def assert_(expected, actual):
    for saving_type, arr in expected.items():
        for _k, expected_val in expected[saving_type].items():
            actual_val = actual[saving_type][_k]

            try:
                actual_val = round(float(actual_val), 2)
            except:
                pass

            msg = f'{saving_type}->{_k}. Expected={expected_val} Actual={actual_val}'

            assert expected_val == actual_val, msg


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

    assert_(expect, actual)


def test_savings_only(_data_savings_only):
    expect = {
        'Saving1': {
            'past_amount': 1.25,
            'past_fee': 0.25,
            'incomes': 4.75,
            'fees': 0.75,
            'invested': 4.0,
        },
        'Saving2': {
            'past_amount': 0.25,
            'past_fee': 0.0,
            'incomes': 2.50,
            'fees': 0.25,
            'invested': 2.25,
        },
    }

    actual = StatsSavings(1999, _data_savings_only).balance

    assert_(expect, actual)


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

    assert_(expect, actual)


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

    assert_(expect, actual)


def test_savings_cloce_only(_data_savings_close):
    actual = StatsSavings(1999, _data_savings_close).balance

    expect = {
        'Saving1': {
            'past_amount': -0.25,
            'past_fee': 0.0,
            'incomes': -0.5,
            'fees': 0.0,
            'invested': -0.5,
        },
        'Saving2': {
            'past_amount': 0.0,
            'past_fee': 0.0,
            'incomes': 0.0,
            'fees': 0.0,
            'invested': 0.0,
        },
    }

    assert_(expect, actual)


def test_savings_empty():
    actual = StatsSavings(1, {}).balance

    assert actual.empty


def test_savings_worth(_savings_worth):
    actual = StatsSavings(1999, _savings_worth).balance

    expect = {
        'Saving1': {
            'incomes': 4.75,
            'invested': 4.0,
            'market_value': 0.15,
            'profit_incomes_proc': -96.84,
            'profit_incomes_sum': -4.6,
            'profit_invested_proc': -96.25,
            'profit_invested_sum': -3.85,
        },
        'Saving2': {
            'incomes': 2.50,
            'invested': 2.25,
            'market_value': 6.15,
            'profit_incomes_proc': 146.0,
            'profit_incomes_sum': 3.65,
            'profit_invested_proc': 173.33,
            'profit_invested_sum': 3.9,
        },
    }

    assert_(expect, actual)
