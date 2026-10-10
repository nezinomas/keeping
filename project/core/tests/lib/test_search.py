from datetime import date
from operator import and_, or_

import factory
import pytest
from django.db.models.signals import post_save
from hypothesis import assume, example, given
from hypothesis import strategies as st

from ....books.services.search import search_books
from ....books.tests.factories import BookFactory
from ....expenses.services.search import search_expenses
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.services.search import search_incomes
from ....incomes.tests.factories import IncomeFactory
from ...lib import search

NOTHING = {"category": [], "year": 0, "month": 0, "remark": []}

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
    "search_str, expect, combine",
    [
        pytest.param(
            "~!@#$%^&*()_+-=[]{}|;:,./<>?\\ x1",
            {**NOTHING, "category": ["_-."], "remark": ["_-."]},
            or_,
            id="symbols_removed",
        ),
        pytest.param(
            "-r ab1~! c!d2",
            {**NOTHING, "remark": ["ab1", "cd2"]},
            and_,
            id="digits_and_spaces_kept",
        ),
    ],
)
def test_parse_search_keeps_word_characters_only(search_str, expect, combine):
    assert search.parse_search(search_str) == (expect, combine)


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
@example(category=None, year=None, month=None, remark=None, long_names=False)
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
    expect = NOTHING | {
        key: long_enough(value) if isinstance(value, list) else value
        for key, value in given_.items()
        if value is not None
    }

    assert search.parse_search(text) == (expect, and_)


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
    words = long_enough(before + after)
    year, month, *_ = first or later or (0, 0)
    expect = {"category": words, "year": year, "month": month or 0, "remark": words}

    assert search.parse_search(text) == (expect, or_)


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "factory_class, search_func, date_field",
    [
        pytest.param(ExpenseFactory, search_expenses, "date", id="expense"),
        pytest.param(IncomeFactory, search_incomes, "date", id="income"),
        pytest.param(BookFactory, search_books, "started", id="book"),
    ],
)
def test_search_orders_newest_first(main_user, factory_class, search_func, date_field):
    factory_class(**{date_field: date(1000, 1, 1)})
    factory_class()

    q = search_func(main_user, "remark")

    assert q[0][date_field] == date(1999, 1, 1)
    assert q[1][date_field] == date(1000, 1, 1)
