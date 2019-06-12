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
