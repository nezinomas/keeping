from datetime import date

import factory
import pytest
from django.db.models.signals import post_save
from hypothesis import assume, example, given
from hypothesis import strategies as st

from ....books.tests.factories import BookFactory
from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory
from ...lib import search

NOTHING = {"category": None, "year": None, "month": None, "remark": None}

# a word never starts with a dash, or it would be read as a flag
WORD = st.from_regex(r"[a-z_][a-z_.-]{0,5}", fullmatch=True)
WORDS = st.lists(WORD, min_size=1, max_size=4)
DATE_TOKEN_PARTS = st.tuples(
    st.integers(1000, 9999),
    st.none() | st.integers(1, 12),
    st.sampled_from([".", "-"]),
    st.none() | st.integers(1, 28),
).map(lambda d: (d[0], d[1], d[2], d[3] if d[1] else None))


def long_enough(words):
    return [word for word in words if len(word) > 2]


def date_token(year, month, separator, day):
    token = f"{year}"
    if month:
        token += f"{separator}{month:02d}"
    if day:
        token += f"{separator}{day:02d}"
    return token


@pytest.mark.parametrize(
    "search_str, expect, search_type",
    [
        pytest.param(
            "~!@#$%^&*()_+-=[]{}|;:,./<>?\\ x1",
            {**NOTHING, "category": ["_-."], "remark": ["_-."]},
            "no_args",
            id="symbols_removed",
        ),
        pytest.param(
            "-r ab1~! c!d2",
            {**NOTHING, "remark": ["ab1", "cd2"]},
            "with_args",
            id="digits_and_spaces_kept",
        ),
        pytest.param(None, NOTHING, "no_args", id="nothing_given"),
    ],
)
def test_parse_search_keeps_word_characters_only(search_str, expect, search_type):
    assert search.parse_search(search_str) == (expect, search_type)


@pytest.mark.parametrize(
    "dictionary, key, default_value, expect",
    [
        ({"a": 1}, "a", "x", 1),
        ({"a": 1}, "b", "x", "x"),
    ],
)
def test_get_from_dictionary(dictionary, key, default_value, expect):
    assert search._get_value(dictionary, key, default_value) == expect


FLAG_NAMES = {
    "category": ("-c", "-category"),
    "year": ("-y", "-year"),
    "month": ("-m", "-month"),
    "remark": ("-r", "-remark"),
}


@given(
    category=st.none() | WORDS,
    year=st.none() | st.integers(0, 9999),
    month=st.none() | st.integers(0, 99),
    remark=st.none() | WORDS,
    long_names=st.booleans(),
)
@example(category=["x"], year=None, month=None, remark=None, long_names=False)
@example(category=["xxx"], year=None, month=None, remark=None, long_names=False)
@example(category=["x"], year=None, month=None, remark=None, long_names=True)
@example(category=["xxx"], year=None, month=None, remark=None, long_names=True)
@example(category=["x", "y"], year=None, month=None, remark=None, long_names=False)
@example(category=["xxx", "yyy"], year=None, month=None, remark=None, long_names=False)
@example(category=None, year=1, month=None, remark=None, long_names=False)
@example(category=None, year=1, month=None, remark=None, long_names=True)
@example(category=None, year=None, month=1, remark=None, long_names=False)
@example(category=None, year=None, month=1, remark=None, long_names=True)
@example(category=None, year=None, month=None, remark=["xxx", "yyy"], long_names=False)
@example(category=None, year=None, month=None, remark=["xxx"], long_names=True)
@example(category=["x"], year=1, month=2, remark=["xxx"], long_names=False)
@example(category=["xxx"], year=1, month=2, remark=["xxx"], long_names=False)
@example(category=["x", "y"], year=1, month=2, remark=["xxx"], long_names=True)
@example(category=["xxx", "yyy"], year=1, month=2, remark=["xxx"], long_names=True)
@example(
    category=["xx", "yyy"], year=2000, month=1, remark=["xx", "yyy"], long_names=False
)
@example(
    category=["xxx", "yyy"],
    year=2000,
    month=1,
    remark=["xxx", "yyy"],
    long_names=False,
)
@example(category=["xxx", "yyy"], year=2000, month=1, remark=None, long_names=False)
@example(category=None, year=2000, month=1, remark=["xxx", "yyy"], long_names=False)
def test_parse_search_with_args(category, year, month, remark, long_names):
    given_ = {"category": category, "year": year, "month": month, "remark": remark}
    text = " ".join(
        f"{FLAG_NAMES[key][long_names]} "
        + (" ".join(value) if isinstance(value, list) else str(value))
        for key, value in given_.items()
        if value is not None
    )
    expect = {
        key: long_enough(value) if isinstance(value, list) else value
        for key, value in given_.items()
    }

    assert search.parse_search(text) == (expect, "with_args")


@given(
    before=st.lists(WORD, max_size=3),
    after=st.lists(WORD, max_size=3),
    first=st.none() | DATE_TOKEN_PARTS,
    later=st.none() | DATE_TOKEN_PARTS,
)
@example(before=["xxx"], after=[], first=None, later=None)
@example(before=["xxx", "yyy"], after=[], first=None, later=None)
@example(before=["xxx"], after=[], first=(1111, None, ".", None), later=None)
@example(before=[], after=[], first=(2000, None, ".", None), later=None)
@example(before=[], after=[], first=(2000, 1, ".", None), later=None)
@example(before=[], after=[], first=(2000, 1, ".", 2), later=None)
@example(before=[], after=[], first=(2000, 1, "-", None), later=None)
@example(before=[], after=[], first=(2000, 1, "-", 2), later=None)
@example(before=["xxx"], after=["yyy"], first=(2000, 1, "-", 2), later=None)
@example(before=["xxx"], after=["yyy"], first=(2000, 1, ".", 2), later=None)
@example(
    before=["xxx"], after=["yyy"], first=(2000, 1, ".", 2), later=(1111, 11, ".", None)
)
@example(before=["type_a"], after=[], first=None, later=None)
@example(before=["type-a"], after=[], first=None, later=None)
@example(before=["type.a"], after=[], first=None, later=None)
@example(
    before=["type.a"], after=[], first=(2000, 1, ".", None), later=(3000, 2, ".", None)
)
@example(before=["ab", "abc"], after=[], first=None, later=None)
@example(before=["ab"], after=[], first=(2000, 1, ".", None), later=None)
def test_parse_search_no_args(before, after, first, later):
    dates = [date_token(*d) for d in (first, later) if d]
    assume(before + after + dates)
    text = " ".join(before + dates[:1] + after + dates[1:])
    words = long_enough(before + after) if before + after else None
    year, month, *_ = first or later or (None, None)
    expect = {"category": words, "year": year, "month": month, "remark": words}

    assert search.parse_search(text) == (expect, "no_args")


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "_search, expect",
    [
        (
            "1999",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-y 1999",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        ("1999.1", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("1999-1", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("-y 1999 -m 1", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("3000", []),
        ("a", []),
        ("ab", []),
        (
            "type_a",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-c type_a",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "type_a name_b",
            [
                {"type": "Type_B", "name": "Name_B", "remark": "WWW"},
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-c type_a name_b",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
            ],
        ),
        (
            "type_a xxx",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        ("-c type_a -r xxx", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("-c type_a name_a -r www", []),
        (
            "-c type_a name_a -r xxx",
            [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "1999 name_a",
            [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-y 1999 -c name_a",
            [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        pytest.param(
            "-c žvaigž",
            [
                {"type": "Žvaigždė", "name": "Ąžuolas", "remark": "ąčęėįšųūž"},
            ],
            marks=pytest.mark.xfail(
                strict=True,
                reason="SQLite icontains folds ASCII only; MariaDB collation folds",
            ),
        ),
        pytest.param(
            "-c ąžuo",
            [
                {"type": "Žvaigždė", "name": "Ąžuolas", "remark": "ąčęėįšųūž"},
            ],
            marks=pytest.mark.xfail(
                strict=True,
                reason="SQLite icontains folds ASCII only; MariaDB collation folds",
            ),
        ),
        (
            "-r ąčęėįšųūž",
            [
                {"type": "Žvaigždė", "name": "Ąžuolas", "remark": "ąčęėįšųūž"},
            ],
        ),
    ],
)
def test_expense_search(main_user, _search, expect):
    ExpenseFactory(
        date=date(1999, 1, 1),
        expense_type=ExpenseTypeFactory(title="Type_A"),
        expense_name=ExpenseNameFactory(title="Name_A"),
        remark="XXX",
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        expense_type=ExpenseTypeFactory(title="Type_A"),
        expense_name=ExpenseNameFactory(title="Name_B"),
        remark="YYY",
    )
    ExpenseFactory(
        date=date(2000, 1, 1),
        expense_type=ExpenseTypeFactory(title="Type_B"),
        expense_name=ExpenseNameFactory(title="Name_A"),
        remark="ZZZ",
    )
    ExpenseFactory(
        date=date(2000, 2, 1),
        expense_type=ExpenseTypeFactory(title="Type_B"),
        expense_name=ExpenseNameFactory(title="Name_B"),
        remark="WWW",
    )
    ExpenseFactory(
        date=date(2001, 2, 1),
        expense_type=ExpenseTypeFactory(title="Žvaigždė"),
        expense_name=ExpenseNameFactory(title="Ąžuolas"),
        remark="ąčęėįšųūž",
    )

    q = search.search_expenses(main_user, _search)

    for row, expected in zip(q, expect, strict=True):
        assert row["expense_type__title"] == expected["type"]
        assert row["expense_name__title"] == expected["name"]
        assert row["remark"] == expected["remark"]


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "factory_class, search_func, date_field",
    [
        pytest.param(ExpenseFactory, search.search_expenses, "date", id="expense"),
        pytest.param(IncomeFactory, search.search_incomes, "date", id="income"),
        pytest.param(BookFactory, search.search_books, "started", id="book"),
    ],
)
def test_search_orders_newest_first(main_user, factory_class, search_func, date_field):
    factory_class(**{date_field: date(1000, 1, 1)})
    factory_class()

    q = search_func(main_user, "remark")

    assert q[0][date_field] == date(1999, 1, 1)
    assert q[1][date_field] == date(1000, 1, 1)


FOUND = ["Income Type"]


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "_search, income_types",
    [
        ("1999", FOUND),
        ("-y 1999", FOUND),
        ("1999.1", FOUND),
        ("1999-1", FOUND),
        ("-y 1999 -m 1", FOUND),
        ("2000", []),
        ("-y 2000", []),
        ("a", []),
        ("ab", []),
        ("type", FOUND),
        ("-c type", FOUND),
        ("remark", FOUND),
        ("-r remark", FOUND),
        ("1999.1 type", FOUND),
        ("1999-1 type", FOUND),
        ("-y 1999 -m 1 -c type", FOUND),
    ],
)
def test_incomes_search(main_user, _search, income_types):
    IncomeFactory()
    IncomeFactory(
        date=date(3333, 1, 1), income_type=IncomeTypeFactory(title="Y"), remark="ZZZ"
    )

    actual = [
        (row["date"], row["income_type__title"])
        for row in search.search_incomes(main_user, _search)
    ]

    assert actual == [(date(1999, 1, 1), title) for title in income_types]


BOOK = ("Author", "Book Title", "Remark")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "_search, books",
    [
        ("1999", [BOOK]),
        ("-y1999", [BOOK]),
        ("1999.1", [BOOK]),
        ("1999-1", [BOOK]),
        ("-y 1999 -m 1", [BOOK]),
        ("2000", []),
        ("-y 2000", []),
        ("a", []),
        ("ab", []),
        ("auth", [BOOK]),
        ("-c auth", [BOOK]),
        ("titl", [BOOK]),
        ("-c titl", [BOOK]),
        ("remark", [BOOK]),
        ("-r remark", [BOOK]),
        ("1999.1 auth", [BOOK]),
        ("1999-1 auth", [BOOK]),
        ("-r 1999 -m 1 -c auth", []),
        ("-y 1999 -m 1 -c auth", [BOOK]),
        ("1999.1 titl", [BOOK]),
        ("1999-1 titl", [BOOK]),
        ("-y 1999 -m 1 -c titl", [BOOK]),
    ],
)
def test_books_search(main_user, _search, books):
    BookFactory()
    BookFactory(started=date(3333, 1, 1), author="A", title="T", remark="ZZZ")

    actual = [
        (row["started"], row["author"], row["title"], row["remark"])
        for row in search.search_books(main_user, _search)
    ]

    assert actual == [(date(1999, 1, 1), *book) for book in books]
