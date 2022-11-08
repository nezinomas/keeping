from decimal import Decimal
from types import SimpleNamespace

import pytest

from ..services.chart_summary import ChartSummaryService


def test_chart_incomes_context():
    data = SimpleNamespace(
        incomes=[],
        salary=[
            {'sum': Decimal('12'), 'year': 1998},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert 'records' in actual
    assert 'chart_title' in actual
    assert 'categories' in actual
    assert 'incomes' in actual
    assert 'incomes_title' in actual
    assert 'salary' in actual
    assert 'salary_title' in actual


@pytest.mark.freeze_time('1999-1-1')
def test_chart_incomes_salary_years():
    data = SimpleNamespace(
        incomes=[],
        salary=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('10'), 'year': 1999},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual['categories'] == [1998, 1999]


@pytest.mark.freeze_time('1999-1-1')
def test_chart_incomes_salary():
    data = SimpleNamespace(
        incomes=[],
        salary=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('10'), 'year': 1999},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_incomes()


    assert actual['salary'] == [1.0, 10.0]


@pytest.mark.freeze_time('1999-1-1')
def test_chart_incomes_incomes():
    data = SimpleNamespace(
        incomes=[
            {'sum': Decimal('24'), 'year': 1998},
            {'sum': Decimal('12'), 'year': 1999},
        ],
        salary=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('10'), 'year': 1999},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_incomes()


    assert actual['incomes'] == [2.0, 12.0]


@pytest.mark.freeze_time('1999-1-1')
def test_chart_incomes_records():
    data = SimpleNamespace(
        incomes=[
            {'sum': Decimal('12'), 'year': 1999},
        ],
        salary=[
            {'sum': Decimal('10'), 'year': 1999},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual['records'] == 1


@pytest.mark.freeze_time('1999-1-1')
def test_chart_incomes_records_no_data():
    data = SimpleNamespace(
        incomes=[],
        salary=[],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual['records'] == 0

    assert 'chart_title' not in actual
    assert 'categories' not in actual
    assert 'incomes' not in actual
    assert 'incomes_title' not in actual
    assert 'salary' not in actual
    assert 'salary_title' not in actual


def test_chart_balance_context():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {'sum': Decimal('12'), 'year': 1998},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert 'records' in actual
    assert 'chart_title' in actual
    assert 'categories' in actual
    assert 'incomes' in actual
    assert 'incomes_title' in actual
    assert 'expenses' in actual
    assert 'expenses_title' in actual


def test_chart_balance_no_data():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['records'] == 0
    assert 'chart_title' not in actual
    assert 'categories' not in actual
    assert 'incomes' not in actual
    assert 'incomes_title' not in actual
    assert 'expenses' not in actual
    assert 'expenses_title' not in actual


def test_chart_balance_records_only_incomes():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {'sum': Decimal('12'), 'year': 1998},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['records'] == 1


def test_chart_balance_records_only_expenses():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        expenses=[
            {'sum': Decimal('12'), 'year': 1998},
        ]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['records'] == 1


def test_chart_balance_records():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {'sum': Decimal('12'), 'year': 1998},
        ],
        expenses=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('24'), 'year': 1999},
        ]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['records'] == 1


def test_chart_balance_categories_only_incomes():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('24'), 'year': 1999},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['categories'] == [1998, 1999]


def test_chart_balance_categories_only_expenses():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        expenses=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('24'), 'year': 1999},
        ]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['categories'] == [1998, 1999]


def test_chart_balance_categories():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('24'), 'year': 1999},
        ],
        expenses=[
            {'sum': Decimal('12'), 'year': 2000},
        ]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['categories'] == [1998, 1999]


def test_chart_balance_incomes():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('24'), 'year': 1999},
        ],
        expenses=[]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['incomes'] == [12.0, 24.0]


def test_chart_balance_expenses():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        expenses=[
            {'sum': Decimal('12'), 'year': 1998},
            {'sum': Decimal('24'), 'year': 1999},
        ]
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual['expenses'] == [12.0, 24.0]
