from decimal import Decimal

import pytest
from mock import patch

from ..services.chart_summary_expenses import ChartSummaryExpensesService

pytestmark = pytest.mark.django_db

GET_YEARS = \
    'project.bookkeeping.services.chart_summary_expenses.\
    ChartSummaryExpensesService.\
    _get_years'


@pytest.fixture
def _types():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'X'},
    ]


@pytest.fixture
def _names():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'A', 'root': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'B', 'root': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'B', 'root': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'A', 'root': 'X'},
    ]

@patch(GET_YEARS, return_value=[1, 2])
def test_categories(mock_years):
    obj = ChartSummaryExpensesService()

    actual = obj.categories

    assert actual == [1, 2]


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data__types(mock_years, _types):
    obj = ChartSummaryExpensesService(
        types=_types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect



@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data__types_year_out_of_range(mock_years, _types):
    _types.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = ChartSummaryExpensesService(
        types=_types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data__types_no_data(mock_years):
    obj = ChartSummaryExpensesService()

    actual = obj.serries_data

    assert actual == []


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_names(mock_years, _names):
    obj = ChartSummaryExpensesService(
        names=_names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_names_year_out_of_range(mock_years, _names):
    _names.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = ChartSummaryExpensesService(
        names=_names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_data_full(mock_years, _types, _names):
    obj = ChartSummaryExpensesService(
        types=_types,
        names=_names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


@patch(GET_YEARS, return_value=[1, 2, 3, 4])
def test_serries_data_remove_empty_columns(mock_years):
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

    obj = ChartSummaryExpensesService(
        types=_types,
        remove_empty_columns=True
    )

    assert obj.categories == [1, 3]
    assert obj.serries_data == [
        {'name': 'X', 'data': [1.0, 3.0]},
        {'name': 'Y', 'data': [2.0, 4.0]},
    ]


@patch(GET_YEARS, return_value=[1, 2])
def test_serries_data_remove_empty_columns_no_data(mock_years):
    obj = ChartSummaryExpensesService(
        remove_empty_columns=True
    )

    assert obj.categories == [1, 2]
    assert obj.serries_data == []


@patch(GET_YEARS, return_value=[])
def test_serries_data_remove_empty_columns_no_data_all(mock_years):
    obj = ChartSummaryExpensesService(
        remove_empty_columns=True
    )

    assert obj.categories == []
    assert obj.serries_data == []


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_total_column(mock_years, _types):
    obj = ChartSummaryExpensesService(
        types=_types
    )

    actual = obj.total_col
    expect = {'X': 20.0, 'Y': 14.0}

    assert actual == expect


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_total_row(mock_years, _types):
    obj = ChartSummaryExpensesService(
        types=_types
    )

    actual = obj.total_row
    expect = [7.0, 12.0, 15.0]

    assert actual == expect


@patch(GET_YEARS, return_value=[2000, 2001, 2002])
def test_serries_total(mock_years, _types):
    obj = ChartSummaryExpensesService(
        types=_types
    )

    actual = obj.total

    assert actual == 34.0
