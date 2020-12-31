from types import SimpleNamespace

import pytest
from freezegun import freeze_time
from mock import patch

from ..context import yday, years


@freeze_time('2006-01-01')
def test_years(rf):
    expect = {'years': [2007, 2006]}
    r = rf.get('/fake/')

    actual = years(r)

    assert len(actual['years']) == 2
    assert expect == actual


@freeze_time('2020-6-6')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'year, expect',
    [
        (1999, {'yday': 365, 'ydays': 365}),
        (2016, {'yday': 366, 'ydays': 366}),
        (2020, {'yday': 158, 'ydays': 366}),
    ]
)
def test_yday(year, expect, rf, get_user):
    get_user.year = year

    r = rf.get('fake')

    actual = yday(r)

    assert actual == expect


@freeze_time('2020-1-1')
@patch('project.core.lib.utils.get_user', return_value=SimpleNamespace())
def test_yday_anonymous_user(mck, rf):
    r = rf.get('fake')

    actual = yday(r)

    assert actual == {'yday': 1, 'ydays': 366}
