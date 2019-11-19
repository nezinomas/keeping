import pytest
from freezegun import freeze_time

from ..context import years


@freeze_time('2006-01-01')
def test_years(rf):
    expect = {'years': [2007, 2006]}
    r = rf.get('/fake/')

    actual = years(r)

    assert len(actual['years']) == 2
    assert expect == actual
