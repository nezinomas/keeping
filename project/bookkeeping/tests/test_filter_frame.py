import pytest

from ..lib.filter_frame import FilterDf as T


@pytest.mark.xfail(raises=Exception)
def test_no_data_exists():
    actual = T(1111, None)


def test_empty_data_property_exists():
    actual = T(1111, dict()).savings

    assert not actual


def test_data(_saving_data):
    actual = T(1970, _saving_data).savings

    assert 1.25 == actual.price[0]
