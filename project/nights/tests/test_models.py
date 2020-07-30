from ..factories import NightFactory


# ----------------------------------------------------------------------------
#                                                                        Night
# ----------------------------------------------------------------------------
def test_night_str():
    actual = NightFactory.build()

    assert str(actual) == '1999-01-01: 1'
