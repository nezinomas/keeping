import pytest
from ..lib.filter_frame import FilterDf as T


@pytest.mark.xfail(raises=Exception)
def test_no_data_exists():
    actual = T(1111, None)


def test_empty_data_property_exists():
    actual = T(1111, dict()).savings

    assert not actual


def test_data(_data_savings):
    actual = T(1970, _data_savings).savings

    assert 100.0 == actual.price[2]
