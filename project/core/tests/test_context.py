from datetime import date
from types import SimpleNamespace

import pytest
import time_machine
from mock import patch

from ...journals.factories import JournalFactory
from ...users.factories import UserFactory
from ..context import context_months, yday, years


@time_machine.travel('2006-01-01')
@pytest.mark.disable_get_user_patch
def test_years(rf):
    expect = {'years': [2007, 2006]}
    r = rf.get('/fake/')

    actual = years(r)

    assert len(actual['years']) == 2
    assert expect == actual


@pytest.mark.django_db
@pytest.mark.disable_get_user_patch
@time_machine.travel('2006-01-01')
@patch('project.core.lib.utils.get_user')
def test_year_first_record_from_journal(mck, rf):
    jrn = JournalFactory(first_record=date(2004, 1, 1))
    usr = UserFactory(journal=jrn)
    mck.return_value = usr

    r = rf.get('/fake/')

    actual = years(r)
    expect = [2007, 2006, 2005, 2004]

    assert expect == actual['years']


@time_machine.travel('2020-6-6')
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


@time_machine.travel('2020-1-1')
@patch('project.core.lib.utils.get_user', return_value=SimpleNamespace())
def test_yday_anonymous_user(mck, rf):
    r = rf.get('fake')

    actual = yday(r)

    assert actual == {'yday': 1, 'ydays': 366}


@time_machine.travel('1974-1-1')
def test_context_months(rf):
    r = rf.get('/fake/')

    actual = context_months(r)

    assert len(actual['context_months']) == 12
    assert actual['context_months'][0] == date(1974, 1, 1)
