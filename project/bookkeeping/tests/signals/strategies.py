from datetime import datetime
from types import SimpleNamespace

from hypothesis import strategies as st

CATEGORY = st.integers(1, 3)
YEAR = st.integers(1995, 1999)
AMOUNT = st.integers(0, 10**6)


def owner(pk, closed=None):
    return SimpleNamespace(pk=pk, closed=closed)


TYPES = tuple(owner(pk) for pk in (1, 2, 3))


def rows(column, **extra):
    return st.fixed_dictionaries(
        {"category_id": CATEGORY, "year": YEAR, column: AMOUNT} | extra
    )


HAVE = st.lists(
    rows("have", latest_check=st.just(datetime(1995, 1, 1))),
    max_size=6,
    unique_by=lambda x: (x["category_id"], x["year"]),
)


def worth(have, row):
    checked = [
        x
        for x in have
        if x["category_id"] == row["category_id"] and x["year"] <= row["year"]
    ]
    return max(checked, key=lambda x: x["year"])["have"] if checked else 0
