from decimal import Decimal

import pytest
from mock import patch

from ..services.chart_summary_expenses import ChartSummaryExpensesService

pytestmark = pytest.mark.django_db

GET_YEARS = \
    'project.bookkeeping.services.chart_summary_expenses.' \
    'ChartSummaryExpensesService._get_years'

GET_TYPES = \
    'project.bookkeeping.services.chart_summary_expenses.' \
    'ChartSummaryExpensesService._get_type_sum_by_year'

GET_NAMES = \
    'project.bookkeeping.services.chart_summary_expenses.' \
    'ChartSummaryExpensesService._get_name_sum_by_year'


def _types():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'X'},
    ]


def _names():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'A', 'root': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'B', 'root': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'B', 'root': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'A', 'root': 'X'},
    ]


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=None)
@patch(GET_YEARS, return_value=[1, 2])
def test_categories(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService()

    actual = obj.categories

    assert actual == [1, 2]


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=_types())
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_types(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1'])

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES)
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_types_year_out_of_range(mock_years, mock_types, mock_names):
    types = _types()
    types.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})
    mock_types.return_value = types

    obj = ChartSummaryExpensesService(['1'])

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=None)
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_types_no_data(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1'])

    actual = obj.serries_data

    assert actual == []


@patch(GET_NAMES, return_value=_names())
@patch(GET_TYPES, return_value=None)
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_names(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1:1'])

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


@patch(GET_NAMES)
@patch(GET_TYPES, return_value=None)
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_names_year_out_of_range(mock_years, mock_types, mock_names):
    names = _names()
    names.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})
    mock_names.return_value = names

    obj = ChartSummaryExpensesService(['1:1'])

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


@patch(GET_NAMES, return_value=_names())
@patch(GET_TYPES, return_value=_types())
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_full(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1', '1:1'])

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES)
@patch(GET_YEARS, return_value=[1, 2, 3, 4])
def test_serries_data_remove_empty_columns(mock_years, mock_types, mock_names):
    _types = [
        {'year': 1, 'sum': Decimal('1'), 'title': 'X'},
        {'year': 1, 'sum': Decimal('2'), 'title': 'Y'},
        {'year': 2, 'sum': Decimal('0'), 'title': 'X'},
        {'year': 2, 'sum': Decimal('0'), 'title': 'Y'},
        {'year': 3, 'sum': Decimal('3'), 'title': 'X'},
        {'year': 3, 'sum': Decimal('4'), 'title': 'Y'},
        {'year': 4, 'sum': Decimal('0'), 'title': 'X'},
        {'year': 4, 'sum': Decimal('0'), 'title': 'Y'},
    ]
    mock_types.return_value = _types

    obj = ChartSummaryExpensesService(['1'], remove_empty_columns=True)

    assert obj.categories == [1, 3]
    assert obj.serries_data == [
        {'name': 'X', 'data': [1.0, 3.0]},
        {'name': 'Y', 'data': [2.0, 4.0]},
    ]


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=None)
@patch(GET_YEARS, return_value=[1, 2])
def test_serries_data_remove_empty_columns_no_data(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(remove_empty_columns=True)

    assert obj.categories == [1, 2]
    assert obj.serries_data == []


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=None)
@patch(GET_YEARS, return_value=[])
def test_serries_data_remove_empty_columns_no_data_all(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(remove_empty_columns=True)

    assert obj.categories == []
    assert obj.serries_data == []


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=_types())
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_total_column(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1'])

    actual = obj.total_col
    expect = {'X': 20.0, 'Y': 14.0}

    assert actual == expect


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=_types())
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_total_row(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1'])

    actual = obj.total_row
    expect = [7.0, 12.0, 15.0]

    assert actual == expect


@patch(GET_NAMES, return_value=None)
@patch(GET_TYPES, return_value=_types())
@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_total(mock_years, mock_types, mock_names):
    obj = ChartSummaryExpensesService(['1'])

    actual = obj.total

    assert actual == 34.0
