from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import time_machine

from ....accounts.tests.factories import AccountFactory
from ....expenses.forms import ExpenseForm
from ....expenses.tests.factories import ExpenseNameFactory
from ....incomes.forms import IncomeForm
from ....incomes.tests.factories import IncomeTypeFactory

pytestmark = pytest.mark.django_db

_VILNIUS = ZoneInfo("Europe/Vilnius")
_OCTOBER_2026 = datetime(2026, 10, 12, 12, 0, tzinfo=_VILNIUS)
_NEW_YEAR_2027 = datetime(2027, 1, 1, 1, 0, tzinfo=_VILNIUS)


def _expense_form(user, posted):
    name = ExpenseNameFactory()
    data = {
        "date": posted,
        "price": 112,
        "quantity": 1,
        "expense_type": name.parent.pk,
        "expense_name": name.pk,
        "account": AccountFactory().pk,
    }
    return ExpenseForm(user=user, data=data)


def _income_form(user, posted):
    data = {
        "date": posted,
        "price": "1.0",
        "account": AccountFactory().pk,
        "income_type": IncomeTypeFactory().pk,
    }
    return IncomeForm(user=user, data=data)


@pytest.mark.parametrize("bound_form", [_expense_form, _income_form])
@pytest.mark.parametrize(
    ("today", "posted", "errors"),
    [
        (_OCTOBER_2026, "2024-06-01", {}),
        (_OCTOBER_2026, "2027-12-31", {}),
        (
            _OCTOBER_2026,
            "2028-01-01",
            {"date": ["Metai negali būti vėlesni nei 2027"]},
        ),
        (_NEW_YEAR_2027, "2028-01-01", {}),
        (
            _NEW_YEAR_2027,
            "2029-01-01",
            {"date": ["Metai negali būti vėlesni nei 2028"]},
        ),
    ],
    ids=["past", "next_year", "year_after_next", "new_year_local", "new_year_after"],
)
def test_date_no_later_than_next_calendar_year(
    main_user, bound_form, today, posted, errors
):
    # a selected year apart from today's: the old message named it + 1
    main_user.year = 2024

    with time_machine.travel(today):
        assert bound_form(main_user, posted).errors == errors
