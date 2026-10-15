from datetime import date

import pytest

from ....accounts.tests.factories import AccountFactory
from ....books.forms import BookTargetForm
from ....books.tests.factories import BookTargetFactory
from ....drinks.forms import DrinkTargetForm
from ....drinks.tests.factories import DrinkTargetFactory
from ....expenses.forms import ExpenseForm
from ....expenses.tests.factories import ExpenseNameFactory
from ....incomes.forms import IncomeForm
from ....incomes.tests.factories import IncomeTypeFactory

pytestmark = pytest.mark.django_db

_OCTOBER_2026 = date(2026, 10, 12)
_NEW_YEAR_2027 = date(2027, 1, 1)


def _expense_form(user, today, posted):
    name = ExpenseNameFactory()
    data = {
        "date": posted,
        "price": 112,
        "quantity": 1,
        "expense_type": name.parent.pk,
        "expense_name": name.pk,
        "account": AccountFactory().pk,
    }
    return ExpenseForm(user=user, today=today, data=data)


def _income_form(user, today, posted):
    data = {
        "date": posted,
        "price": "1.0",
        "account": AccountFactory().pk,
        "income_type": IncomeTypeFactory().pk,
    }
    return IncomeForm(user=user, today=today, data=data)


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
    ids=["past", "next_year", "year_after_next", "new_year", "new_year_after"],
)
def test_date_no_later_than_next_calendar_year(
    main_user, bound_form, today, posted, errors
):
    # a selected year apart from today's: the old message named it + 1
    main_user.year = 2024

    assert bound_form(main_user, today, posted).errors == errors


@pytest.mark.parametrize(
    ("form_class", "factory", "data"),
    [
        (BookTargetForm, BookTargetFactory, {"quantity": 5}),
        (DrinkTargetForm, DrinkTargetFactory, {"quantity": 5, "drink_type": "beer"}),
    ],
    ids=["books", "drinks"],
)
def test_a_target_keeps_its_year_when_edited(main_user, form_class, factory, data):
    target = factory(year=1999)

    form = form_class(
        user=main_user,
        today=_OCTOBER_2026,
        instance=target,
        data={"year": 1999, **data},
    )

    assert form.errors == {}
