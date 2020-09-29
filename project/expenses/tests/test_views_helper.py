from datetime import date

import pytest

from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..helpers import views as H


def test_get_year():
    search = 'test1 2000.10 test2 1999 test3 300.11.11 test4 2015-15-15 test5'

    _date, _ = H.parse_search_input(search)

    assert _date == '2000.10'


def test_get_year_no_number():
    search = 'test1'

    _date, _ = H.parse_search_input(search)

    assert not _date


def test_get_strings():
    search = 'test1 2000.10 test2 1999.12.12 test3'

    _, _str = H.parse_search_input(search)

    assert _str == ['test1', 'test2', '1999.12.12', 'test3']


def test_get_strings_no_strings():
    search = '3000'

    _, _str = H.parse_search_input(search)

    assert not _str


def test_get_nothing():
    search = '300 xxx'

    _d, _s = H.parse_search_input(search)

    assert not _s
    assert not _d


@pytest.mark.django_db
@pytest.mark.parametrize(
    'search, cnt, expense_type, expense_name',
    [
        ('1999', 1, 'Expense Type', 'Expense Name'),
        ('1999.1', 1, 'Expense Type', 'Expense Name'),
        ('1999-1', 1, 'Expense Type', 'Expense Name'),
        ('2000', 0, None, None),
        ('name', 1, 'Expense Type', 'Expense Name'),
        ('type', 1, 'Expense Type', 'Expense Name'),
        ('remark', 1, 'Expense Type', 'Expense Name'),
        ('1999 name', 1, 'Expense Type', 'Expense Name'),
        ('1999 name', 1, 'Expense Type', 'Expense Name'),
        ('1999.1 name', 1, 'Expense Type', 'Expense Name'),
        ('1999-1 name', 1, 'Expense Type', 'Expense Name'),
        ('1999.1 type', 1, 'Expense Type', 'Expense Name'),
        ('1999-1 type', 1, 'Expense Type', 'Expense Name'),
    ]
)
def test_search(search, cnt, expense_type, expense_name, get_user):
    ExpenseFactory()
    ExpenseFactory(
        date=date(3333, 1, 1),
        expense_name=ExpenseNameFactory(title='X'),
        expense_type=ExpenseTypeFactory(title='Y'),
        remark='ZZZ'
    )

    q = H.search(search)
    assert q.count() == cnt

    if q:
        q = q[0]

        assert q.date == date(1999, 1, 1)
        assert q.expense_type.title == expense_type
        assert q.expense_name.title == expense_name


@pytest.mark.django_db
def test_search_ordering(get_user):
    ExpenseFactory(date=date(1000, 1, 1))
    ExpenseFactory()

    q = H.search('remark')

    assert q[0].date == date(1999, 1, 1)
    assert q[1].date == date(1000, 1, 1)
