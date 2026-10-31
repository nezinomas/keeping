from datetime import date

import pytest
import time_machine
from django.contrib.auth.models import AnonymousUser

from ..context import context_months, nav_active, yday, years

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


def test_years_of_an_anonymous_user_are_empty(rf):
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


@pytest.mark.parametrize(
    "path, expect",
    [
        pytest.param("/", {"bookkeeping"}, id="year_menu_on_the_root_only"),
        pytest.param("/month/", {"month"}, id="month"),
        pytest.param("/detailed/expenses/", {"detailed"}, id="detailed_not_expenses"),
        pytest.param("/expenses/data/all/", {"expenses"}, id="expenses_tab"),
        pytest.param("/summary/expenses/", {"charts"}, id="charts_not_expenses"),
        pytest.param("/plans/expenses/", {"plans"}, id="plans_not_expenses"),
        pytest.param("/incomes/", {"incomes"}, id="incomes"),
        pytest.param("/incomes/data/", set(), id="incomes_tab_exact_path"),
        pytest.param("/transactions/", {"transactions"}, id="transactions"),
        pytest.param("/savings/type/", {"savings"}, id="savings_page"),
        pytest.param("/summary/savings/", {"charts"}, id="charts_not_savings"),
        pytest.param("/plans/savings/", {"plans"}, id="plans_not_savings"),
        pytest.param("/detailed/savings/", {"detailed"}, id="detailed_not_savings"),
        pytest.param("/transactions/lists/", set(), id="transactions_list_exact"),
        pytest.param("/debts/", {"debts"}, id="debts"),
        pytest.param("/debts/lend/lists/", set(), id="debts_list_exact_path"),
        pytest.param("/books/data/all/", {"books"}, id="books_tab"),
        pytest.param("/drinks/", {"drinks"}, id="drinks"),
        pytest.param("/drinks/data/", set(), id="drinks_tab_exact_path"),
        pytest.param("/counts/c/count-type/", {"counts"}, id="counts"),
        pytest.param("/settings/users/", {"settings"}, id="settings"),
    ],
)
def test_nav_active_names_the_items_a_path_lights(rf, path, expect):
    assert nav_active(rf.get(path)) == {"nav_active": expect}
