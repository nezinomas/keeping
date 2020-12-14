from ..factories import CountFactory


# ----------------------------------------------------------------------------
#                                                                        Count
# ----------------------------------------------------------------------------
def test_count_str():
    actual = CountFactory.build()

    assert str(actual) == '1999-01-01: 1'
