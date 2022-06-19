from decimal import Decimal

import pytest

from ..services.chart_summary_expenses import ChartSummaryExpensesService

pytestmark = pytest.mark.django_db


@pytest.fixture
def types():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'X'},
    ]


@pytest.fixture
def names():
    return [
        {'year': 2000, 'sum': Decimal('5'), 'title': 'A', 'root': 'X'},
        {'year': 2000, 'sum': Decimal('2'), 'title': 'B', 'root': 'Y'},
        {'year': 2001, 'sum': Decimal('12'), 'title': 'B', 'root': 'Y'},
        {'year': 2002, 'sum': Decimal('15'), 'title': 'A', 'root': 'X'},
    ]


def test_helper_compare_categories():
    obj = ChartSummaryExpensesService(years=[1, 2])

    actual = obj.categories

    assert actual == [1, 2]


def test_helper_compare_serries_data_types(types):
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


def test_helper_compare_serries_data_types_year_out_of_range(types):
    types.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_helper_compare_serries_data_types_no_data():
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002]
    )

    actual = obj.serries_data

    assert actual == []


def test_helper_compare_serries_data_names(names):
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]

    assert actual == expect


def test_helper_compare_serries_data_names_year_out_of_range(names):
    names.append({'year': 2003, 'sum': Decimal('25'), 'title': 'XXX'})

    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_helper_compare_serries_data_full(types, names):
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        types=types,
        names=names
    )

    actual = obj.serries_data
    expect = [
        {'name': 'X', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y', 'data': [2.0, 12.0, 0.0]},
        {'name': 'X/A', 'data': [5.0, 0.0, 15.0]},
        {'name': 'Y/B', 'data': [2.0, 12.0, 0.0]},
    ]
    assert actual == expect


def test_helper_compare_serries_data_remove_empty_columns():
    types = [
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
        years=[1, 2, 3, 4],
        types=types,
        remove_empty_columns=True
    )

    assert obj.categories == [1, 3]
    assert obj.serries_data == [
        {'name': 'X', 'data': [1.0, 3.0]},
        {'name': 'Y', 'data': [2.0, 4.0]},
    ]


def test_helper_compare_serries_data_remove_empty_columns_no_data():
    obj = ChartSummaryExpensesService(
        years=[1, 2],
        remove_empty_columns=True
    )

    assert obj.categories == [1, 2]
    assert obj.serries_data == []


def test_helper_compare_serries_data_remove_empty_columns_no_data_all():
    obj = ChartSummaryExpensesService(
        years=[],
        remove_empty_columns=True
    )

    assert obj.categories == []
    assert obj.serries_data == []


def test_helper_compare_serries_total_column(types):
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.total_col
    expect = {'X': 20.0, 'Y': 14.0}

    assert actual == expect


def test_helper_compare_serries_total_row(types):
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.total_row
    expect = [7.0, 12.0, 15.0]

    assert actual == expect


def test_helper_compare_serries_total(types):
    obj = ChartSummaryExpensesService(
        years=[2000, 2001, 2002],
        types=types
    )

    actual = obj.total

    assert actual == 34.0
