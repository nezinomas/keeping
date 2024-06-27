from datetime import date

import pytest

from ...books.factories import BookFactory
from ...expenses.factories import (ExpenseFactory, ExpenseNameFactory,
                                   ExpenseTypeFactory)
from ...incomes.factories import IncomeFactory, IncomeTypeFactory
from ..lib import search as H


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
            "-y 1",
            {"category": None, "year": 1, "month": None, "remark": None}
        ),
        (
            "-year 1",
            {"category": None, "year": 1, "month": None, "remark": None}
        ),
        (
            "-m 1",
            {"category": None, "year": None, "month": 1, "remark": None}
        ),
        (
            "-month 1",
            {"category": None, "year": None, "month": 1, "remark": None},
        ),
        (
            "-r xxx yyy",
            {"category": None, "year": None, "month": None, "remark": ["xxx", "yyy"]},
        ),
        (
            "-remark xxx",
            {"category": None, "year": None, "month": None, "remark": ["xxx"]},
        ),
        (
            "-c x -y 1 -m 2 -r xxx",
            {"category": ["x"], "year": 1, "month": 2, "remark": ["xxx"]},
        ),
        (
            "-category x y -year 1 -month 2 -remark xxx",
            {"category": ["x", "y"], "year": 1, "month": 2, "remark": ["xxx"]},
        ),
        pytest.param(
            "xxx 1111",
            {"category": None, "year": None, "month": None, "remark": None},
            marks=pytest.mark.xfail(reason='argparse.ArgumentError'),
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
        (
            "type_a",
            {"category": ["type_a"], "year": None, "month": None, "remark": ["type_a"]}
        ),
        (
            "type-a",
            {"category": ["type-a"], "year": None, "month": None, "remark": ["type-a"]}
        ),
        (
            "type.a",
            {"category": ["type.a"], "year": None, "month": None, "remark": ["type.a"]}
        ),
        (
            "type.a 2000.01 3000.02",
            {"category": ["type.a"], "year": 2000, "month": 1, "remark": ["type.a"]}
        ),
    ],
)
def test_parse_search_no_args(search, expect):
    assert expect == H.parse_search_no_args(search)


@pytest.mark.parametrize(
    "search_dict, expect",
    [
        (
            {"category": ["xx", "yyy"], "year": 2000, "month": 1, "remark": ["xx", "yyy"]},
            {"category": ["yyy"], "year": 2000, "month": 1, "remark": ["yyy"]},
        ),
        (
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": ["xxx", "yyy"]},
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": ["xxx", "yyy"]},
        ),
        (
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": None},
            {"category": ["xxx", "yyy"], "year": 2000, "month": 1, "remark": None},
        ),
        (
            {"category": None, "year": 2000, "month": 1, "remark": ["xxx", "yyy"]},
            {"category": None, "year": 2000, "month": 1, "remark": ["xxx", "yyy"]},
        ),
    ],
)
def test_filter_short_search_words(search_dict, expect):
    assert expect == H.filter_short_search_words(search_dict)


# ---------------------------------------------------------------------------------------
#                                                                                 Expense
# ---------------------------------------------------------------------------------------
@pytest.mark.django_db
@pytest.mark.parametrize(
    'search, expect',
    [
        (
            '1999', [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '-y 1999', [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '1999.1', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '1999-1', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '-y 1999 -m 1', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '3000', []
        ),
        (
            'type_a', [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '-c type_a', [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            'type_a name_b', [
                {"type": "Type_B", "name": "Name_B", "remark": "WWW"},
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '-c type_a name_b', [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
            ]
        ),
        (
            'type_a xxx', [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '-c type_a -r xxx', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"}
            ]
        ),
        (
            '-c type_a name_a -r www', []
        ),
        (
            '-c type_a name_a -r xxx', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ]
        ),
        (
            '1999 name_a', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ]
        ),
        (
            '-y 1999 -c name_a', [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ]
        ),
    ]
)
def test_expense_search(search, expect):
    ExpenseFactory(
        date=date(1999, 1, 1),
        expense_type=ExpenseTypeFactory(title='Type_A'),
        expense_name=ExpenseNameFactory(title='Name_A'),
        remark='XXX'
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        expense_type=ExpenseTypeFactory(title='Type_A'),
        expense_name=ExpenseNameFactory(title='Name_B'),
        remark='YYY'
    )
    ExpenseFactory(
        date=date(2000, 1, 1),
        expense_type=ExpenseTypeFactory(title='Type_B'),
        expense_name=ExpenseNameFactory(title='Name_A'),
        remark='ZZZ'
    )
    ExpenseFactory(
        date=date(2000, 2, 1),
        expense_type=ExpenseTypeFactory(title='Type_B'),
        expense_name=ExpenseNameFactory(title='Name_B'),
        remark='WWW'
    )

    q = H.search_expenses(search)

    for i in range(len(expect)):
        assert q[i].expense_type.title == expect[i]["type"]
        assert q[i].expense_name.title == expect[i]["name"]
        assert q[i].remark == expect[i]["remark"]


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
        ('-y 1999', 1, 'Income Type'),
        ('1999.1', 1, 'Income Type'),
        ('1999-1', 1, 'Income Type'),
        ('-y 1999 -m 1', 1, 'Income Type'),
        ('2000', 0, None),
        ('-y 2000', 0, None),
        ('type', 1, 'Income Type'),
        ('-c type', 1, 'Income Type'),
        ('remark', 1, 'Income Type'),
        ('-r remark', 1, 'Income Type'),
        ('1999.1 type', 1, 'Income Type'),
        ('1999-1 type', 1, 'Income Type'),
        ('-y 1999 -m 1 -c type', 1, 'Income Type'),
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
        ('-y1999', 'Author', 'Book Title', 'Remark'),
        ('1999.1', 'Author', 'Book Title', 'Remark'),
        ('1999-1', 'Author', 'Book Title', 'Remark'),
        ('-y 1999 -m 1', 'Author', 'Book Title', 'Remark'),
        ('2000', None, None, None),
        ('-y 2000', None, None, None),
        ('auth', 'Author', 'Book Title', 'Remark'),
        ('-c auth', 'Author', 'Book Title', 'Remark'),
        ('titl', 'Author', 'Book Title', 'Remark'),
        ('-c titl', 'Author', 'Book Title', 'Remark'),
        ('remark', 'Author', 'Book Title', 'Remark'),
        ('-r remark', 'Author', 'Book Title', 'Remark'),
        ('1999.1 auth', 'Author', 'Book Title', 'Remark'),
        ('1999-1 auth', 'Author', 'Book Title', 'Remark'),
        ('-r 1999 -m 1 -c auth', 'Author', 'Book Title', 'Remark'),
        ('1999.1 titl', 'Author', 'Book Title', 'Remark'),
        ('1999-1 titl', 'Author', 'Book Title', 'Remark'),
        ('-y 1999 -m 1 -c titl', 'Author', 'Book Title', 'Remark'),
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
