from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from pandas import Timestamp as pdTime

from ..lib.year_balance import YearBalance


@pytest.fixture()
def _incomes():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]


@pytest.fixture()
def _savings():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(1.0)},
    ]


@pytest.fixture()
def _savings_close():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5)},
    ]


@pytest.fixture()
def _expenses():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(1.75)},
    ]


@pytest.fixture()
def _borrow():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal('.25')},
    ]


@pytest.fixture()
def _borrow_return():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal('.15')},
    ]


@pytest.fixture()
def _lend():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal('1')},
    ]


@pytest.fixture()
def _lend_return():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal('0.5')},
    ]


@pytest.fixture()
def _money_flow():
    return Decimal(1)


@pytest.fixture
def _expect():
    val = [
        {
            'date': pdTime(date(1999, 1, 1)),
            'incomes': 5.5,
            'expenses': 1.75,
            'balance': 3.75,
            'savings': 1.0,
            'savings_close': 0.5,
            'borrow': 0.25,
            'borrow_return': 0.15,
            'lend': 1.0,
            'lend_return': 0.5,
            'money_flow': 3.85
        }, {
            'date': pdTime(date(1999, 2, 1)),
            'incomes': 1.25,
            'expenses': 0.0,
            'balance': 1.25,
            'savings': 0.0,
            'savings_close': 0.0,
            'borrow': 0.0,
            'borrow_return': 0.0,
            'lend': 0.0,
            'lend_return': 0.0,
            'money_flow': 5.1
        }
    ]

    # same dictionaries for march - december
    for i in range(3, 13):
        item = {
            'date': pdTime(date(1999, i, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'borrow': 0.0,
            'borrow_return': 0.0,
            'lend': 0.0,
            'lend_return': 0.0,
            'money_flow': 5.1
        }
        val.append(item)

    return val


def test_months_balance(_incomes, _expenses,
                        _savings, _savings_close,
                        _borrow, _borrow_return,
                        _lend, _lend_return,
                        _money_flow, _expect):
    data = {
        'incomes':_incomes,
        'expenses':_expenses,
        'savings':_savings,
        'savings_close':_savings_close,
        'borrow':_borrow,
        'borrow_return':_borrow_return,
        'lend':_lend,
        'lend_return':_lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual == _expect


def test_balance_when_wrong_data_column_names():
    data = {
        'xxx': [{'date': date(1999, 1, 1), 'sum': Decimal(5.5)}],
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).balance

    assert 'xxx' not in actual[0].keys()


def test_months_balance_only_saving_close(_incomes, _expenses,
                                          _savings_close,
                                          _money_flow):

    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'savings_close': _savings_close,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual[0]['savings_close'] == 0.5
    assert actual[0]['money_flow'] == 5.25

    assert actual[1]['savings_close'] == 0.0
    assert actual[1]['money_flow'] == 6.5

    for i in range(3, 12):
        assert actual[i]['savings_close'] == 0.0
        assert actual[i]['money_flow'] == 6.5


def test_months_balance_only_savings(_incomes, _expenses,
                                     _savings,
                                     _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'savings': _savings,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual[0]['savings'] == 1.0
    assert actual[0]['money_flow'] == 3.75

    assert actual[1]['savings'] == 0.0
    assert actual[1]['money_flow'] == 5.0

    for i in range(3, 12):
        assert actual[i]['savings'] == 0.0
        assert actual[i]['money_flow'] == 5.0


def test_months_balance_only_borrow(_incomes, _expenses,
                                     _borrow,
                                     _money_flow):
    data = {
        'incomes':_incomes,
        'expenses':_expenses,
        'borrow':_borrow,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual[0]['borrow'] == 0.25
    assert actual[0]['money_flow'] == 5.0

    assert actual[1]['borrow'] == 0.0
    assert actual[1]['money_flow'] == 6.25

    for i in range(3, 12):
        assert actual[i]['borrow'] == 0.0
        assert actual[i]['money_flow'] == 6.25


def test_months_balance_only_borrow_return(_incomes, _expenses,
                                     _borrow_return,
                                     _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'borrow_return': _borrow_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual[0]['borrow_return'] == 0.15
    assert actual[0]['money_flow'] == 4.6

    assert actual[1]['borrow_return'] == 0.0
    assert actual[1]['money_flow'] == 5.85

    for i in range(3, 12):
        assert actual[i]['borrow_return'] == 0.0
        assert actual[i]['money_flow'] == 5.85


def test_months_balance_only_lend(_incomes, _expenses,
                                     _lend,
                                     _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'lend': _lend,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual[0]['lend'] == 1.0
    assert actual[0]['money_flow'] == 3.75

    assert actual[1]['lend'] == 0.0
    assert actual[1]['money_flow'] == 5.0

    for i in range(3, 12):
        assert actual[i]['lend'] == 0.0
        assert actual[i]['money_flow'] == 5.0


def test_months_balance_only_lend_return(_incomes, _expenses,
                                     _lend_return,
                                     _money_flow):
    data = {
        'incomes':_incomes,
        'expenses':_expenses,
        'lend_return':_lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).balance

    assert actual[0]['lend_return'] == 0.5
    assert actual[0]['money_flow'] == 5.25

    assert actual[1]['lend_return'] == 0.0
    assert actual[1]['money_flow'] == 6.5

    for i in range(3, 12):
        assert actual[i]['lend_return'] == 0.0
        assert actual[i]['money_flow'] == 6.5


def test_months_balance_total_row(_incomes, _expenses,
                                  _savings, _savings_close,
                                  _borrow, _borrow_return,
                                  _lend, _lend_return,
                                  _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'savings': _savings,
        'savings_close': _savings_close,
        'borrow': _borrow,
        'borrow_return': _borrow_return,
        'lend': _lend,
        'lend_return': _lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).total_row

    expect = {
        'incomes': 6.75,
        'expenses': 1.75,
        'balance': 5.0,
        'savings': 1.0,
        'savings_close': 0.5,
        'borrow': 0.25,
        'borrow_return': 0.15,
        'lend': 1.0,
        'lend_return': 0.5,
        'money_flow': 59.95
    }

    assert actual == expect


def test_months_balance_average(_incomes, _expenses,
                                _savings, _savings_close,
                                _borrow, _borrow_return,
                                _lend, _lend_return,
                                _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'savings': _savings,
        'savings_close': _savings_close,
        'borrow': _borrow,
        'borrow_return': _borrow_return,
        'lend': _lend,
        'lend_return': _lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).average

    expect = {
        'incomes': 3.38,
        'expenses': 1.75,
        'balance': 2.5,
        'savings': 1.0,
        'savings_close': 0.5,
        'borrow': 0.25,
        'borrow_return': 0.15,
        'lend': 1.0,
        'lend_return': 0.5,
        'money_flow': 5.0
    }

    assert expect == pytest.approx(actual, rel=1e-2)


def test_amount_start():
    actual = YearBalance(
        year=1999,
        data=None,
        amount_start=10
    ).amount_start

    assert actual == 10


def test_amount_start_none():
    actual = YearBalance(
        year=1999,
        data=None,
        amount_start=None
    ).amount_start

    assert actual == 0.0


def test_amount_end(_incomes, _expenses,
                    _savings, _savings_close,
                    _borrow, _borrow_return,
                    _lend, _lend_return,
                    _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'savings': _savings,
        'savings_close': _savings_close,
        'borrow': _borrow,
        'borrow_return': _borrow_return,
        'lend': _lend,
        'lend_return': _lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).amount_end

    assert actual == 5.1


def test_amount_end_no_money_flow(_incomes, _expenses):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
    )
    del actual._balance['money_flow']

    assert actual.amount_end == 0.0


def test_amount_end_none():
    actual = YearBalance(
        year=1999,
        data=None,
        amount_start=None
    ).amount_end

    assert actual == 0.0


def test_amount_balance(_incomes, _expenses, _money_flow):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).amount_balance

    assert actual == 5.0


def test_balance_none():
    data = {
        'incomes': [],
        'expenses': [],
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).amount_balance

    assert actual == 0.0


def test_balance_income_data(_incomes, _expect):
    data = {
        'incomes': _incomes,
        'expenses': [],
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).income_data

    expect = [x['incomes'] for x in _expect]

    assert actual == expect


def test_balance_expense_data(_expenses, _expect):
    data = {
        'incomes': [],
        'expenses': _expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).expense_data

    expect = [x['expenses'] for x in _expect]

    assert actual == expect


def test_balance_borrow_data(_incomes, _borrow, _expect):
    data = {
        'incomes':_incomes,
        'expenses':[],
        'borrow':_borrow,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).borrow_data

    expect = [x['borrow'] for x in _expect]

    assert actual == expect


def test_balance_borrow_return_data(_incomes, _borrow_return, _expect):
    data = {
        'incomes': _incomes,
        'expenses': [],
        'borrow_return': _borrow_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).borrow_return_data

    expect = [x['borrow_return'] for x in _expect]

    assert actual == expect


def test_balance_lend_data(_incomes, _lend, _expect):
    data = {
        'incomes':_incomes,
        'expenses':[],
        'lend':_lend,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).lend_data

    expect = [x['lend'] for x in _expect]

    assert actual == expect


def test_balance_lend_return_data(_incomes, _lend_return, _expect):
    data = {
        'incomes': _incomes,
        'expenses': [],
        'lend_return': _lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).lend_return_data

    expect = [x['lend_return'] for x in _expect]

    assert actual == expect


def test_balance_money_flow(_incomes, _expenses,
                            _savings, _savings_close,
                            _borrow, _borrow_return,
                            _lend, _lend_return,
                            _money_flow, _expect):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
        'savings': _savings,
        'savings_close': _savings_close,
        'borrow': _borrow,
        'borrow_return': _borrow_return,
        'lend': _lend,
        'lend_return': _lend_return,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=_money_flow
    ).money_flow

    expect = [x['money_flow'] for x in _expect]

    assert actual == expect


def test_avg_incomes(_incomes, _expenses):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).avg_incomes

    assert pytest.approx(actual, rel=1e-2) == 3.38


def test_avg_incomes_none():
    data = {
        'incomes': None,
        'expenses': None,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).avg_incomes

    assert actual == 0.0


def test_avg_expenses(_incomes, _expenses):
    data = {
        'incomes': _incomes,
        'expenses': _expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).avg_expenses

    assert actual == 1.75


def test_avg_expenses_none():
    data = {
        'incomes':None,
        'expenses':None,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).avg_expenses

    assert actual == 0.0


@freeze_time('1999-2-1')
def test_avg_expenses_current_year():
    expenses = [
        {'date': date(1999, 1, 1), 'sum': Decimal('1')},
        {'date': date(1999, 2, 1), 'sum': Decimal('2')},
        {'date': date(1999, 3, 1), 'sum': Decimal('3')},
    ]

    data = {
        'incomes': None,
        'expenses': expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).avg_expenses

    assert actual == 1.5


@freeze_time('2000-2-1')
def test_avg_expenses_not_current_year():
    expenses = [
        {'date': date(1999, 1, 1), 'sum': Decimal('1')},
        {'date': date(1999, 2, 1), 'sum': Decimal('2')},
        {'date': date(1999, 3, 1), 'sum': Decimal('3')},
    ]

    data = {
        'incomes': None,
        'expenses': expenses,
    }

    actual = YearBalance(
        year=1999,
        data=data,
        amount_start=None
    ).avg_expenses

    assert actual == 2.0
