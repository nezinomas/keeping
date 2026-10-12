from datetime import date

import pytest
import time_machine
from django.contrib.auth.models import AnonymousUser

from ..context import context_months, yday, years

pytestmark = pytest.mark.django_db


@time_machine.travel("2006-01-01")
@pytest.mark.parametrize(
    "first_record, expect",
    [
        (date(2005, 2, 3), [2007, 2006, 2005]),
        (date(2004, 2, 3), [2007, 2006, 2005, 2004]),
    ],
)
def test_years_run_from_the_first_record_to_next_year(
    fake_request, first_record, expect
):
    fake_request.user.journal.first_record = first_record

    assert years(fake_request) == {"years": expect}


def test_years_of_an_anonymous_user_are_none(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    assert years(request) == {"years": []}


@time_machine.travel("2020-6-6")
@pytest.mark.parametrize(
    "year, expect",
    [
        (1999, {"yday": 365, "ydays": 365}),
        (2016, {"yday": 366, "ydays": 366}),
        (2020, {"yday": 158, "ydays": 366}),
        (2021, {"yday": 0, "ydays": 365}),
    ],
)
def test_yday_follows_the_users_year(fake_request, year, expect):
    fake_request.user.year = year

    assert yday(fake_request) == expect


@time_machine.travel("2000-1-1")
def test_context_months_are_the_users_year(main_user, rf):
    request = rf.get("/")
    request.user = main_user

    actual = context_months(request)

    assert actual == {"context_months": [date(1999, m, 1) for m in range(1, 13)]}
