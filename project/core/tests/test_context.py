import pytest
from freezegun import freeze_time

from ..context import years


@freeze_time('2006-01-01')
def test_years(rf):
    expect = {'years': [2007, 2006, 2005, 2004]}
    r = rf.get('/fake/')

    actual = years(r)

    assert 4 == len(actual['years'])
    assert expect == actual
