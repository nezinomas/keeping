from hypothesis import strategies as st

CATEGORY = st.integers(1, 3)
YEAR = st.integers(1995, 1999)
AMOUNT = st.integers(0, 10**6)


def rows(column, **extra):
    return st.fixed_dictionaries(
        {"category_id": CATEGORY, "year": YEAR, column: AMOUNT} | extra
    )
