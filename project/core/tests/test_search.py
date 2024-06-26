from datetime import date

import pytest

from ...books.factories import BookFactory
from ...expenses.factories import (ExpenseFactory, ExpenseNameFactory,
                                   ExpenseTypeFactory)
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from ..lib import search as H


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


def test_get_strings_no_data():
    search = None

    _d, _str = H.parse_search_input(search)

    assert not _d
    assert _str == []


def test_search_min_word_length():
    search = 'xx'

    _, _s = H.parse_search_input(search)

    assert _s == ['xx']


def test_sanitize_search_str():
    search = '~!@#$%^&*()_+-=[]{}|;:,./<>?\\ x1'
    actual = H.sanitize_search_str(search)

    assert actual == '_-. x1'


def test_sanitize_search_str_empty():
    search = None
    actual = H.sanitize_search_str(search)

    assert not actual


@pytest.mark.parametrize(
    "search, expect",
    [
        (
            "-c x",
            {"category": ["x"], "year": None, "month": None, "remark": None}
        ),
        (
            "-category x",
            {"category": ["x"], "year": None, "month": None, "remark": None},
        ),
        (
            "-c x y",
            {"category": ["x", "y"], "year": None, "month": None, "remark": None},
        ),
        (
            "-y 1 -c x",
            {"category": ["x"], "year": 1, "month": None, "remark": None}
        ),
        (
            "-year 1 -c x",
            {"category": ["x"], "year": 1, "month": None, "remark": None}
        ),
        (
            "-m 1 -c x",
            {"category": ["x"], "year": None, "month": 1, "remark": None}
        ),
        (
            "-month 1 -c x",
            {"category": ["x"], "year": None, "month": 1, "remark": None},
        ),
        (
            "-r xxx yyy -c x",
            {"category": ["x"], "year": None, "month": None, "remark": ["xxx", "yyy"]},
        ),
        (
            "-remark xxx -c x",
            {"category": ["x"], "year": None, "month": None, "remark": ["xxx"]},
        ),
        (
            "-c x -y 1 -m 2 -r xxx",
            {"category": ["x"], "year": 1, "month": 2, "remark": ["xxx"]},
        ),
        (
            "-category x y -year 1 -month 2 -remark xxx",
            {"category": ["x", "y"], "year": 1, "month": 2, "remark": ["xxx"]},
        ),
    ],
)
def test_parse_search_with_args(search, expect):
    assert expect == H.parse_search_with_args(search)


@pytest.mark.parametrize(
    "search, expect",
    [
        (
            "xxx",
            {"category": ["xxx"], "year": None, "month": None, "remark": ["xxx"]}
        ),
        (
            "xxx yyy",
            {"category": ["xxx", "yyy"], "year": None, "month": None, "remark": ["xxx", "yyy"]},
        ),
        (
            "2000",
            {"category": None, "year": 2000, "month": None, "remark": None}
        ),
        (
            "2000.01",
            {"category": None, "year": 2000, "month": 1, "remark": None}
        ),
        (
            "2000.01.02",
            {"category": None, "year": 2000, "month": 1, "remark": None}
        ),
        (
            "2000-01",
            {"category": None, "year": 2000, "month": 1, "remark": None}
        ),
        (
            "2000-01",
            {"category": None, "year": 2000, "month": 1, "remark": None}
        ),
        (
            "2000-01-02",
            {"category": None, "year": 2000, "month": 1, "remark": None}
        ),
        (
            "xxx 2000-01-02 yyy",
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": ["xxx", "yyy"]}
        ),
        (
            "xxx 2000.01.02 yyy",
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": ["xxx", "yyy"]}
        ),
        (
            "xxx 2000.01.02 yyy 1111.11",
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": ["xxx", "yyy"]}
        ),
    ],
)
def test_parse_search_no_args(search, expect):
    assert expect == H.parse_search_no_args(search)


# ---------------------------------------------------------------------------------------
#                                                                                 Expense
# ---------------------------------------------------------------------------------------
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
def test_expense_search(search, cnt, expense_type, expense_name):
    ExpenseFactory()
    ExpenseFactory(
        date=date(3333, 1, 1),
        expense_name=ExpenseNameFactory(title='X'),
        expense_type=ExpenseTypeFactory(title='Y'),
        remark='ZZZ'
    )

    q = H.search_expenses(search)
    assert q.count() == cnt

    if q:
        q = q[0]

        assert q.date == date(1999, 1, 1)
        assert q.expense_type.title == expense_type
        assert q.expense_name.title == expense_name


@pytest.mark.django_db
def test_expense_search_ordering():
    ExpenseFactory(date=date(1000, 1, 1))
    ExpenseFactory()

    q = H.search_expenses('remark')

    assert q[0].date == date(1999, 1, 1)
    assert q[1].date == date(1000, 1, 1)


# ---------------------------------------------------------------------------------------
#                                                                                 Income
# ---------------------------------------------------------------------------------------
@pytest.mark.django_db
@pytest.mark.parametrize(
    'search, cnt, income_type',
    [
        ('1999', 1, 'Income Type'),
        ('1999.1', 1, 'Income Type'),
        ('1999-1', 1, 'Income Type'),
        ('2000', 0, None),
        ('type', 1, 'Income Type'),
        ('remark', 1, 'Income Type'),
        ('1999.1 type', 1, 'Income Type'),
        ('1999-1 type', 1, 'Income Type'),
    ]
)
def test_search(search, cnt, income_type):
    IncomeFactory()
    IncomeFactory(
        date=date(3333, 1, 1),
        income_type=IncomeTypeFactory(title='Y'),
        remark='ZZZ'
    )

    q = H.search_incomes(search)
    assert q.count() == cnt

    if q:
        q = q[0]

        assert q.date == date(1999, 1, 1)
        assert q.income_type.title == income_type


@pytest.mark.django_db
def test_search_ordering():
    IncomeFactory(date=date(1000, 1, 1))
    IncomeFactory()

    q = H.search_incomes('remark')

    assert q[0].date == date(1999, 1, 1)
    assert q[1].date == date(1000, 1, 1)


# ---------------------------------------------------------------------------------------
#                                                                                    Book
# ---------------------------------------------------------------------------------------
@pytest.mark.django_db
@pytest.mark.parametrize(
    'search, author, title, remark',
    [
        ('1999', 'Author', 'Book Title', 'Remark'),
        ('1999.1', 'Author', 'Book Title', 'Remark'),
        ('1999-1', 'Author', 'Book Title', 'Remark'),
        ('2000', None, None, None),
        ('auth', 'Author', 'Book Title', 'Remark'),
        ('titl', 'Author', 'Book Title', 'Remark'),
        ('remark', 'Author', 'Book Title', 'Remark'),
        ('1999.1 auth', 'Author', 'Book Title', 'Remark'),
        ('1999-1 auth', 'Author', 'Book Title', 'Remark'),
        ('1999.1 titl', 'Author', 'Book Title', 'Remark'),
        ('1999-1 titl', 'Author', 'Book Title', 'Remark'),
    ]
)
def test_search(search, author, title, remark):
    BookFactory()
    BookFactory(
        started=date(3333, 1, 1),
        author='A',
        title='T',
        remark='ZZZ'
    )

    q = H.search_books(search)

    if q:
        q = q[0]

        assert q.started == date(1999, 1, 1)
        assert q.author == author
        assert q.title == title
        assert q.remark == remark


@pytest.mark.django_db
def test_search_ordering():
    BookFactory(started=date(1000, 1, 1))
    BookFactory()

    q = H.search_books('remark')

    assert q[0].started == date(1999, 1, 1)
    assert q[1].started == date(1000, 1, 1)
