import pytest
import time_machine

from ...core.lib.translation import month_names
from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...savings.tests.factories import SavingTypeFactory
from ...users.tests.factories import UserFactory
from ..forms import (
    CopyPlanForm,
    DayPlanForm,
    ExpensePlanForm,
    IncomePlanForm,
    NecessaryPlanForm,
    SavingPlanForm,
)
from ..models import IncomePlan
from ..services.model_services import ModelService
from .factories import (
    DayPlanFactory,
    ExpensePlanFactory,
    IncomePlanFactory,
    NecessaryPlanFactory,
    SavingPlanFactory,
)

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Income Form
# ----------------------------------------------------------------------------
def test_income_init(main_user):
    IncomePlanForm(user=main_user)


def test_income_init_fields(main_user):
    form = IncomePlanForm(user=main_user).as_p()

    assert '<input type="text" name="year"' in form
    assert '<select name="income_type"' in form

    assert '<input type="number" name="january"' in form
    assert '<input type="number" name="february"' in form
    assert '<input type="number" name="march"' in form
    assert '<input type="number" name="april"' in form
    assert '<input type="number" name="may"' in form
    assert '<input type="number" name="june"' in form
    assert '<input type="number" name="july"' in form
    assert '<input type="number" name="august"' in form
    assert '<input type="number" name="september"' in form
    assert '<input type="number" name="october"' in form
    assert '<input type="number" name="november"' in form
    assert '<input type="number" name="december"' in form

    assert '<select name="user"' not in form


@time_machine.travel("1974-01-01")
def test_income_year_initial_value(main_user):
    UserFactory()

    form = IncomePlanForm(user=main_user).as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_income_current_user_types(main_user, second_user):
    IncomeTypeFactory(title="T1")  # user bob, current user
    IncomeTypeFactory(title="T2", journal=second_user.journal)  # user X

    form = IncomePlanForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@pytest.mark.parametrize(
    "year",
    [
        ("1999"),
        (1999),
    ],
)
def test_income_valid_data(year, main_user):
    type_ = IncomeTypeFactory()
    form = IncomePlanForm(
        user=main_user,
        data={
            "year": year,
            "income_type": type_.pk,
            "january": 0.01,
            "february": 0.01,
            "march": 0.01,
            "april": 0.01,
            "may": 0.01,
            "june": 0.01,
            "july": 0.01,
            "august": 0.01,
            "september": 0.01,
            "october": 0.01,
            "november": 0.01,
            "december": 0.01,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 1
    assert data.february == 1
    assert data.march == 1
    assert data.april == 1
    assert data.may == 1
    assert data.june == 1
    assert data.july == 1
    assert data.august == 1
    assert data.september == 1
    assert data.october == 1
    assert data.november == 1
    assert data.december == 1
    assert str(data.income_type) == "Income Type"
    assert data.journal.users.first().username == "bob"


@time_machine.travel("1999-01-01")
def test_income_blank_data(main_user):
    form = IncomePlanForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "income_type" in form.errors


def test_income_unique_together_validation(main_user):
    i = IncomePlanFactory()

    form = IncomePlanForm(
        user=main_user,
        data={
            "year": i.year,
            "income_type": i.income_type.pk,
            "january": 666,
        },
    )

    assert not form.is_valid()

    assert form.errors == {"__all__": ["1999 metai jau turi Income Type planą."]}


def test_income_unique_together_validation_more_than_one(main_user):
    IncomePlanFactory(income_type=IncomeTypeFactory(title="First"))

    type_ = IncomeTypeFactory()
    form = IncomePlanForm(
        user=main_user,
        data={
            "year": 1999,
            "income_type": type_.pk,
            "january": 15,
        },
    )

    assert form.is_valid()


def test_income_negative_number(main_user):
    IncomePlanFactory(income_type=IncomeTypeFactory(title="First"))

    type_ = IncomeTypeFactory()

    data = {
        "year": 1999,
        "income_type": type_.pk,
    }

    # add negative numbet to earch month
    for key, _ in month_names().items():
        data[key.lower()] = -1

    form = IncomePlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_income_inputs_as_string(main_user):
    IncomePlanFactory(income_type=IncomeTypeFactory(title="First"))

    type_ = IncomeTypeFactory()

    data = {
        "year": 1999,
        "income_type": type_.pk,
    }

    # add negative numbet to earch month
    for key, _ in month_names().items():
        data[key.lower()] = "a"

    form = IncomePlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


# ----------------------------------------------------------------------------
#                                                                 Expense Form
# ----------------------------------------------------------------------------
def test_expense_init(main_user):
    ExpensePlanForm(user=main_user)


def test_expense_init_fields(main_user):
    form = ExpensePlanForm(user=main_user).as_p()

    assert '<input type="text" name="year"' in form
    assert '<select name="expense_type"' in form

    assert '<input type="number" name="january"' in form
    assert '<input type="number" name="february"' in form
    assert '<input type="number" name="march"' in form
    assert '<input type="number" name="april"' in form
    assert '<input type="number" name="may"' in form
    assert '<input type="number" name="june"' in form
    assert '<input type="number" name="july"' in form
    assert '<input type="number" name="august"' in form
    assert '<input type="number" name="september"' in form
    assert '<input type="number" name="october"' in form
    assert '<input type="number" name="november"' in form
    assert '<input type="number" name="december"' in form

    assert '<select name="user"' not in form


@time_machine.travel("1974-01-01")
def test_expense_year_initial_value(main_user):
    UserFactory()

    form = ExpensePlanForm(user=main_user).as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_expense_current_user_types(main_user, second_user):
    ExpenseTypeFactory(title="T1")  # user bob, current user
    ExpenseTypeFactory(title="T2", journal=second_user.journal)  # user X

    form = ExpensePlanForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@pytest.mark.parametrize(
    "year",
    [
        ("1999"),
        (1999),
    ],
)
def test_expense_valid_data(year, main_user):
    type_ = ExpenseTypeFactory()
    form = ExpensePlanForm(
        user=main_user,
        data={
            "year": year,
            "expense_type": type_.pk,
            "january": 0.01,
            "february": 0.01,
            "march": 0.01,
            "april": 0.01,
            "may": 0.01,
            "june": 0.01,
            "july": 0.01,
            "august": 0.01,
            "september": 0.01,
            "october": 0.01,
            "november": 0.01,
            "december": 0.01,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 1
    assert data.february == 1
    assert data.march == 1
    assert data.april == 1
    assert data.may == 1
    assert data.june == 1
    assert data.july == 1
    assert data.august == 1
    assert data.september == 1
    assert data.october == 1
    assert data.november == 1
    assert data.december == 1
    assert str(data.expense_type) == "Expense Type"
    assert data.journal.users.first().username == "bob"


@time_machine.travel("1999-01-01")
def test_expense_blank_data(main_user):
    form = ExpensePlanForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "expense_type" in form.errors


def test_expense_unique_together_validation(main_user):
    i = ExpensePlanFactory()

    form = ExpensePlanForm(
        user=main_user,
        data={
            "year": i.year,
            "expense_type": i.expense_type.pk,
            "january": 666,
        },
    )

    assert not form.is_valid()

    assert form.errors == {"__all__": ["1999 metai jau turi Expense Type planą."]}


def test_expense_unique_together_validation_more_than_one(main_user):
    ExpensePlanFactory(expense_type=ExpenseTypeFactory(title="First"))
    t = ExpenseTypeFactory()
    form = ExpensePlanForm(
        user=main_user,
        data={
            "year": 1999,
            "expense_type": t.pk,
            "january": 15,
        },
    )

    assert form.is_valid()


# ----------------------------------------------------------------------------
#                                                                  Saving Form
# ----------------------------------------------------------------------------
def test_saving_init(main_user):
    SavingPlanForm(user=main_user)


def test_saving_init_fields(main_user):
    form = SavingPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year"' in form
    assert '<select name="saving_type"' in form

    assert '<input type="number" name="january"' in form
    assert '<input type="number" name="february"' in form
    assert '<input type="number" name="march"' in form
    assert '<input type="number" name="april"' in form
    assert '<input type="number" name="may"' in form
    assert '<input type="number" name="june"' in form
    assert '<input type="number" name="july"' in form
    assert '<input type="number" name="august"' in form
    assert '<input type="number" name="september"' in form
    assert '<input type="number" name="october"' in form
    assert '<input type="number" name="november"' in form
    assert '<input type="number" name="december"' in form

    assert '<select name="user"' not in form


@time_machine.travel("1974-01-01")
def test_saving_year_initial_value(main_user):
    UserFactory()

    form = SavingPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_saving_current_user_types(main_user, second_user):
    SavingTypeFactory(title="T1")  # user bob, current user
    SavingTypeFactory(title="T2", journal=second_user.journal)  # user X

    form = SavingPlanForm(user=main_user).as_p()

    assert "T1" in form
    assert "T2" not in form


@pytest.mark.parametrize(
    "year",
    [
        ("1999"),
        (1999),
    ],
)
def test_saving_valid_data(year, main_user):
    type_ = SavingTypeFactory()
    form = SavingPlanForm(
        user=main_user,
        data={
            "year": year,
            "saving_type": type_.pk,
            "january": 0.01,
            "february": 0.01,
            "march": 0.01,
            "april": 0.01,
            "may": 0.01,
            "june": 0.01,
            "july": 0.01,
            "august": 0.01,
            "september": 0.01,
            "october": 0.01,
            "november": 0.01,
            "december": 0.01,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 1
    assert data.february == 1
    assert data.march == 1
    assert data.april == 1
    assert data.may == 1
    assert data.june == 1
    assert data.july == 1
    assert data.august == 1
    assert data.september == 1
    assert data.october == 1
    assert data.november == 1
    assert data.december == 1
    assert str(data.saving_type) == "Savings"
    assert data.journal.users.first().username == "bob"


@time_machine.travel("1999-01-01")
def test_saving_blank_data(main_user):
    form = SavingPlanForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "saving_type" in form.errors


def test_saving_unique_together_validation(main_user):
    i = SavingPlanFactory()

    form = SavingPlanForm(
        user=main_user,
        data={
            "year": i.year,
            "saving_type": i.saving_type.pk,
            "january": 666,
        },
    )

    assert not form.is_valid()

    assert form.errors == {"__all__": ["1999 metai jau turi Savings planą."]}


def test_saving_unique_together_validation_more_than_on(main_user):
    SavingPlanFactory(saving_type=SavingTypeFactory(title="First"))

    t = SavingTypeFactory()
    form = SavingPlanForm(
        user=main_user,
        data={
            "year": 1999,
            "saving_type": t.pk,
            "january": 15,
        },
    )

    assert form.is_valid()


def test_saving_form_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingPlanForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert "S2" not in str(form["saving_type"])


def test_saving_form_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingPlanForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert "S2" in str(form["saving_type"])


def test_saving_form_type_closed_in_current_year(main_user):
    main_user.year = 2000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingPlanForm(user=main_user)

    assert "S1" in str(form["saving_type"])
    assert "S2" in str(form["saving_type"])


# ----------------------------------------------------------------------------
#                                                                     Day Form
# ----------------------------------------------------------------------------
def test_day_init(main_user):
    DayPlanForm(user=main_user)


def test_day_init_fields(main_user):
    form = DayPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year"' in form

    assert '<input type="number" name="january"' in form
    assert '<input type="number" name="february"' in form
    assert '<input type="number" name="march"' in form
    assert '<input type="number" name="april"' in form
    assert '<input type="number" name="may"' in form
    assert '<input type="number" name="june"' in form
    assert '<input type="number" name="july"' in form
    assert '<input type="number" name="august"' in form
    assert '<input type="number" name="september"' in form
    assert '<input type="number" name="october"' in form
    assert '<input type="number" name="november"' in form
    assert '<input type="number" name="december"' in form

    assert '<select name="user"' not in form


@time_machine.travel("1974-01-01")
def test_day_year_initial_value(main_user):
    UserFactory()

    form = DayPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year" value="1999"' in form


@pytest.mark.parametrize(
    "year",
    [
        ("1999"),
        (1999),
    ],
)
def test_day_valid_data(year, main_user):
    form = DayPlanForm(
        user=main_user,
        data={
            "year": year,
            "january": 0.01,
            "february": 0.01,
            "march": 0.01,
            "april": 0.01,
            "may": 0.01,
            "june": 0.01,
            "july": 0.01,
            "august": 0.01,
            "september": 0.01,
            "october": 0.01,
            "november": 0.01,
            "december": 0.01,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 1
    assert data.february == 1
    assert data.march == 1
    assert data.april == 1
    assert data.may == 1
    assert data.june == 1
    assert data.july == 1
    assert data.august == 1
    assert data.september == 1
    assert data.october == 1
    assert data.november == 1
    assert data.december == 1
    assert data.journal.users.first().username == "bob"


@time_machine.travel("1999-01-01")
def test_day_blank_data(main_user):
    form = DayPlanForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert "year" in form.errors


def test_day_unique_together_validation(main_user):
    i = DayPlanFactory()

    form = DayPlanForm(
        user=main_user,
        data={
            "year": i.year,
            "january": 666,
        },
    )

    assert not form.is_valid()

    assert form.errors == {"__all__": ["1999 metai jau turi Dienos planą."]}


# ----------------------------------------------------------------------------
#                                                               Necessary Form
# ----------------------------------------------------------------------------
def test_necessary_init(main_user):
    NecessaryPlanForm(user=main_user)


def test_necessary_init_fields(main_user):
    form = NecessaryPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year"' in form
    assert '<select name="expense_type"' in form
    assert '<input type="text" name="title"' in form

    assert '<input type="number" name="january"' in form
    assert '<input type="number" name="february"' in form
    assert '<input type="number" name="march"' in form
    assert '<input type="number" name="april"' in form
    assert '<input type="number" name="may"' in form
    assert '<input type="number" name="june"' in form
    assert '<input type="number" name="july"' in form
    assert '<input type="number" name="august"' in form
    assert '<input type="number" name="september"' in form
    assert '<input type="number" name="october"' in form
    assert '<input type="number" name="november"' in form
    assert '<input type="number" name="december"' in form

    assert '<select name="user"' not in form


@time_machine.travel("1974-01-01")
def test_income_year_initial_value1(main_user):
    UserFactory()

    form = NecessaryPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year" value="1999"' in form


@pytest.mark.parametrize(
    "year",
    [
        ("1999"),
        (1999),
    ],
)
def test_necessary_valid_data(year, main_user):
    expense = ExpenseTypeFactory()
    form = NecessaryPlanForm(
        user=main_user,
        data={
            "year": year,
            "title": "XXX",
            "expense_type": expense.pk,
            "january": 0.01,
            "february": 0.01,
            "march": 0.01,
            "april": 0.01,
            "may": 0.01,
            "june": 0.01,
            "july": 0.01,
            "august": 0.01,
            "september": 0.01,
            "october": 0.01,
            "november": 0.01,
            "december": 0.01,
        },
    )
    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 1
    assert data.february == 1
    assert data.march == 1
    assert data.april == 1
    assert data.may == 1
    assert data.june == 1
    assert data.july == 1
    assert data.august == 1
    assert data.september == 1
    assert data.october == 1
    assert data.november == 1
    assert data.december == 1
    assert data.title == "XXX"
    assert data.journal.users.first().username == "bob"


@time_machine.travel("1999-01-01")
def test_necessary_blank_data(main_user):
    form = NecessaryPlanForm(user=main_user, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "year" in form.errors
    assert "title" in form.errors
    assert "expense_type" in form.errors


def test_necessary_unique_together_validation(main_user):
    i = NecessaryPlanFactory(title="XXX")

    form = NecessaryPlanForm(
        user=main_user,
        data={
            "year": i.year,
            "expense_type": i.expense_type.pk,
            "title": i.title,
            "january": 666,
        },
    )

    assert not form.is_valid()

    assert form.errors == {
        "__all__": ["1999 metai ir Expense Type jau turi XXX planą."]
    }


def test_necessary_unique_titles_but_different_expense_type(main_user):
    e1 = ExpenseTypeFactory(title="E1")
    e2 = ExpenseTypeFactory(title="E2")

    i = NecessaryPlanFactory(title="XXX", expense_type=e1)

    form = NecessaryPlanForm(
        user=main_user,
        data={
            "year": i.year,
            "title": i.title,
            "expense_type": e2.pk,
            "january": 666,
        },
    )

    assert form.is_valid()


def test_necessary_unique_together_validation_more_than_one(main_user):
    i = NecessaryPlanFactory(title="First")

    form = NecessaryPlanForm(
        user=main_user,
        data={
            "year": 1999,
            "expense_type": i.expense_type.pk,
            "title": "XXX",
            "january": 15,
        },
    )

    assert form.is_valid()


# ----------------------------------------------------------------------------
#                                                                    Copy Form
# ----------------------------------------------------------------------------
def test_copy_init(main_user):
    CopyPlanForm(user=main_user)


def test_copy_have_fields(main_user):
    form = CopyPlanForm(user=main_user).as_p()

    assert '<input type="text" name="year_from"' in form
    assert '<input type="text" name="year_to"' in form
    assert '<input type="checkbox" name="income"' in form
    assert '<input type="checkbox" name="expense"' in form
    assert '<input type="checkbox" name="saving"' in form
    assert '<input type="checkbox" name="day"' in form
    assert '<input type="checkbox" name="necessary"' in form


def test_copy_blank_data(main_user):
    form = CopyPlanForm(user=main_user, data={})

    assert not form.is_valid()

    assert form.errors == {
        "year_from": ["Šis laukas yra privalomas."],
        "year_to": ["Šis laukas yra privalomas."],
    }


def test_copy_all_checkboxes_unselected(main_user):
    form = CopyPlanForm(
        user=main_user,
        data={
            "year_from": 1999,
            "year_to": 2000,
        },
    )

    assert not form.is_valid()

    assert form.errors == {"__all__": ["Reikia pažymėti nors vieną planą."]}


def test_copy_empty_from_tables(main_user):
    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert not form.is_valid()

    assert form.errors == {"income": ["Nėra ką kopijuoti."]}


def test_copy_to_table_have_records(main_user):
    IncomePlanFactory(year=1999)
    IncomePlanFactory(year=2000)

    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert not form.is_valid()

    assert form.errors == {"income": ["2000 metai jau turi planus."]}


def test_copy_to_table_have_records_from_empty(main_user):
    IncomePlanFactory(year=2000)

    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert not form.is_valid()

    assert form.errors == {
        "income": ["Nėra ką kopijuoti.", "2000 metai jau turi planus."]
    }


def test_copy_data(main_user):
    IncomePlanFactory(year=1999)

    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert form.is_valid()

    form.save()

    data = ModelService(IncomePlan, main_user).year(2000)

    assert data.exists()
    assert data[0].year == 2000
