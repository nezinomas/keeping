from datetime import datetime

import pytest
import time_machine
from django.forms import HiddenInput
from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ..forms import (
    CopyPlanForm,
    DayPlanForm,
    ExpensePlanForm,
    IncomePlanForm,
    NecessaryPlanForm,
    SavingPlanForm,
)
from ..services.model_services import IncomePlanModelService
from ..tests.factories import (
    DayPlan,
    DayPlanFactory,
    ExpensePlan,
    ExpensePlanFactory,
    ExpenseTypeFactory,
    IncomePlan,
    IncomePlanFactory,
    IncomeTypeFactory,
    NecessaryPlan,
    NecessaryPlanFactory,
    SavingPlan,
    SavingPlanFactory,
    SavingTypeFactory,
)

pytestmark = pytest.mark.django_db

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


# -------------------------------------------------------------------------------------
#                                                                      Income Plan Form
# -------------------------------------------------------------------------------------


def test_income_does_not_render_user_select(main_user):
    form = IncomePlanForm(user=main_user)
    rendered_html = form.as_p()

    assert '<select name="user"' not in rendered_html
    assert 'name="user"' not in rendered_html


@pytest.mark.parametrize("month", MONTHS)
def test_income_initialization(main_user, month):
    form = IncomePlanForm(user=main_user)

    assert month in form.fields

    assert isinstance(form.fields["journal"].widget, HiddenInput)
    assert form.fields["journal"].initial == main_user.journal


@time_machine.travel("1999-01-01")
def test_income_blank_data(main_user):
    form = IncomePlanForm(user=main_user, data={})

    assert not form.is_valid()
    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "income_type" in form.errors


def test_income_unique_together_validation(main_user):
    existing_plan = IncomePlanFactory(year=1999)

    form = IncomePlanForm(
        user=main_user,
        data={
            "year": existing_plan.year,
            "income_type": existing_plan.income_type.pk,
            "january": 666.00,
        },
    )

    assert not form.is_valid()

    expected_msg = _("%(year)s year already has %(title)s plan.") % {
        "year": existing_plan.year,
        "title": existing_plan.income_type.title,
    }
    assert form.errors == {"__all__": [expected_msg]}


def test_income_unique_together_validation_more_than_one(main_user):
    """Tests that uniqueness doesn't block valid distinct inputs."""
    IncomePlanFactory(
        year=1999,
        income_type=IncomeTypeFactory(title="First"),
        journal=main_user.journal,
    )

    new_type = IncomeTypeFactory(title="Second")
    form = IncomePlanForm(
        user=main_user,
        data={
            "year": 1999,
            "income_type": new_type.pk,
            "january": 15.00,
        },
    )

    assert form.is_valid()


def test_income_negative_number(main_user):
    type_ = IncomeTypeFactory()

    data = {
        "year": 1999,
        "income_type": type_.pk,
    }

    # Add a negative number to every single month
    for key, _ in month_names().items():
        data[key.lower()] = -1.00

    form = IncomePlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_income_save_converts_to_cents(main_user):
    income_type = IncomeTypeFactory()

    form_data = {
        "year": 1999,
        "income_type": income_type.pk,
        "january": 0.01,
        "march": 2.5,
    }
    form = IncomePlanForm(data=form_data, user=main_user)

    assert form.is_valid()
    form.save()

    assert IncomePlan.objects.count() == 2

    jan_plan = IncomePlan.objects.get(month=1)
    mar_plan = IncomePlan.objects.get(month=3)

    assert jan_plan.price == 1
    assert jan_plan.year == 1999
    assert jan_plan.income_type == income_type

    assert mar_plan.price == 250
    assert mar_plan.year == 1999
    assert mar_plan.income_type == income_type


def test_income_loads_initial_and_converts_from_cents(main_user):
    income_type = IncomeTypeFactory()
    plan_jan = IncomePlanFactory(month=1, price=15_000, income_type=income_type)
    IncomePlanFactory(month=12, price=30_000, income_type=income_type)

    form = IncomePlanForm(instance=plan_jan, user=main_user)

    assert form.initial["year"] == 1999
    assert form.initial["income_type"] == income_type.pk

    # 4. Assert conversion to standard floats for the frontend
    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert form.initial.get("february") is None

    # 5. Assert grouping fields are locked to prevent orphaned rows
    assert form.fields["year"].disabled is True
    assert form.fields["income_type"].disabled is True


def test_income_updates_and_deletes_rows(main_user):
    """Tests updates, deletions, and cents conversions handle correctly."""

    income_type = IncomeTypeFactory()

    plan_jan = IncomePlan.objects.create(
        year=2026,
        month=1,
        price=10000,
        income_type=income_type,
        journal=main_user.journal,
    )
    IncomePlan.objects.create(
        year=2026,
        month=2,
        price=20000,
        income_type=income_type,
        journal=main_user.journal,
    )

    updated_data = {
        "year": 2026,
        "income_type": income_type.pk,
        "january": 150.00,  # Updated
        "february": "",  # Cleared -> Should Delete
        "march": 300.00,  # New -> Should Create
    }

    form = IncomePlanForm(data=updated_data, instance=plan_jan, user=main_user)
    assert form.is_valid()
    form.save()

    # 3. Assert correct DB state in CENTS
    assert IncomePlan.objects.count() == 2
    assert IncomePlan.objects.filter(month=2).exists() is False
    assert IncomePlan.objects.get(month=1).price == 15000  # Updated to 15000
    assert IncomePlan.objects.get(month=3).price == 30000  # Created as 30000


def test_income_plan_form_prevents_cross_category_pollution(main_user):
    salary_type = IncomeTypeFactory(title="Salary", journal=main_user.journal)
    gift_type = IncomeTypeFactory(title="Gift", journal=main_user.journal)

    # Create a Salary plan for Jan (Target instance)
    salary_instance = IncomePlanFactory(
        year=2026,
        month=1,
        price=100000,
        income_type=salary_type,
        journal=main_user.journal,
    )

    # Create a Gift plan for Feb (Noise)
    IncomePlanFactory(
        year=2026,
        month=2,
        price=50000,
        income_type=gift_type,
        journal=main_user.journal,
    )

    form = IncomePlanForm(user=main_user, instance=salary_instance)

    assert form.initial["january"] == 1000.0  # 100000 cents -> 1000.0 float
    assert form.initial.get("february") is None, "Cross-category pollution detected!"


# -------------------------------------------------------------------------------------
#                                                                      Expense Plan Form
# -------------------------------------------------------------------------------------


def test_expense_does_not_render_user_select(main_user):
    form = ExpensePlanForm(user=main_user)
    rendered_html = form.as_p()

    assert '<select name="user"' not in rendered_html
    assert 'name="user"' not in rendered_html


@pytest.mark.parametrize("month", MONTHS)
def test_expense_initialization(main_user, month):
    form = ExpensePlanForm(user=main_user)

    assert month in form.fields

    assert isinstance(form.fields["journal"].widget, HiddenInput)
    assert form.fields["journal"].initial == main_user.journal


@time_machine.travel("1999-01-01")
def test_expense_blank_data(main_user):
    form = ExpensePlanForm(user=main_user, data={})

    assert not form.is_valid()
    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "expense_type" in form.errors


def test_expense_unique_together_validation(main_user):
    existing_plan = ExpensePlanFactory(year=1999)

    form = ExpensePlanForm(
        user=main_user,
        data={
            "year": existing_plan.year,
            "expense_type": existing_plan.expense_type.pk,
            "january": 666.00,
        },
    )

    assert not form.is_valid()

    expected_msg = _("%(year)s year already has %(title)s plan.") % {
        "year": existing_plan.year,
        "title": existing_plan.expense_type.title,
    }
    assert form.errors == {"__all__": [expected_msg]}


def test_expense_unique_together_validation_more_than_one(main_user):
    """Tests that uniqueness doesn't block valid distinct inputs."""
    ExpensePlanFactory(
        year=1999,
        expense_type=ExpenseTypeFactory(title="First"),
        journal=main_user.journal,
    )

    new_type = ExpenseTypeFactory(title="Second")
    form = ExpensePlanForm(
        user=main_user,
        data={
            "year": 1999,
            "expense_type": new_type.pk,
            "january": 15.00,
        },
    )

    assert form.is_valid()


def test_expense_negative_number(main_user):
    type_ = ExpenseTypeFactory()

    data = {
        "year": 1999,
        "expense_type": type_.pk,
    }

    # Add a negative number to every single month
    for key, _ in month_names().items():
        data[key.lower()] = -1.00

    form = ExpensePlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_expense_save_converts_to_cents(main_user):
    expense_type = ExpenseTypeFactory()

    form_data = {
        "year": 1999,
        "expense_type": expense_type.pk,
        "january": 0.01,
        "march": 2.5,
    }
    form = ExpensePlanForm(data=form_data, user=main_user)

    assert form.is_valid()
    form.save()

    assert ExpensePlan.objects.count() == 2

    jan_plan = ExpensePlan.objects.get(month=1)
    mar_plan = ExpensePlan.objects.get(month=3)

    assert jan_plan.price == 1
    assert jan_plan.year == 1999
    assert jan_plan.expense_type == expense_type

    assert mar_plan.price == 250
    assert mar_plan.year == 1999
    assert mar_plan.expense_type == expense_type


def test_expense_loads_initial_and_converts_from_cents(main_user):
    expense_type = ExpenseTypeFactory()
    plan_jan = ExpensePlanFactory(month=1, price=15_000, expense_type=expense_type)
    ExpensePlanFactory(month=12, price=30_000, expense_type=expense_type)

    form = ExpensePlanForm(instance=plan_jan, user=main_user)

    assert form.initial["year"] == 1999
    assert form.initial["expense_type"] == expense_type.pk

    # 4. Assert conversion to standard floats for the frontend
    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert form.initial.get("february") is None

    # 5. Assert grouping fields are locked to prevent orphaned rows
    assert form.fields["year"].disabled is True
    assert form.fields["expense_type"].disabled is True


def test_expense_updates_and_deletes_rows(main_user):
    """Tests updates, deletions, and cents conversions handle correctly."""

    expense_type = ExpenseTypeFactory()

    plan_jan = ExpensePlan.objects.create(
        year=2026,
        month=1,
        price=10000,
        expense_type=expense_type,
        journal=main_user.journal,
    )
    ExpensePlan.objects.create(
        year=2026,
        month=2,
        price=20000,
        expense_type=expense_type,
        journal=main_user.journal,
    )

    updated_data = {
        "year": 2026,
        "expense_type": expense_type.pk,
        "january": 150.00,  # Updated
        "february": "",  # Cleared -> Should Delete
        "march": 300.00,  # New -> Should Create
    }

    form = ExpensePlanForm(data=updated_data, instance=plan_jan, user=main_user)
    assert form.is_valid()
    form.save()

    # 3. Assert correct DB state in CENTS
    assert ExpensePlan.objects.count() == 2
    assert ExpensePlan.objects.filter(month=2).exists() is False
    assert ExpensePlan.objects.get(month=1).price == 15000  # Updated to 15000
    assert ExpensePlan.objects.get(month=3).price == 30000  # Created as 30000


def test_expense_plan_form_prevents_cross_category_pollution(main_user):
    salary_type = ExpenseTypeFactory(title="Salary", journal=main_user.journal)
    gift_type = ExpenseTypeFactory(title="Gift", journal=main_user.journal)

    # Create a Salary plan for Jan (Target instance)
    salary_instance = ExpensePlanFactory(
        year=2026,
        month=1,
        price=100000,
        expense_type=salary_type,
        journal=main_user.journal,
    )

    # Create a Gift plan for Feb (Noise)
    ExpensePlanFactory(
        year=2026,
        month=2,
        price=50000,
        expense_type=gift_type,
        journal=main_user.journal,
    )

    form = ExpensePlanForm(user=main_user, instance=salary_instance)

    assert form.initial["january"] == 1000.0  # 100000 cents -> 1000.0 float
    assert form.initial.get("february") is None, "Cross-category pollution detected!"


# -------------------------------------------------------------------------------------
#                                                                      Saving Plan Form
# -------------------------------------------------------------------------------------


def test_saving_does_not_render_user_select(main_user):
    form = SavingPlanForm(user=main_user)
    rendered_html = form.as_p()

    assert '<select name="user"' not in rendered_html
    assert 'name="user"' not in rendered_html


@pytest.mark.parametrize("month", MONTHS)
def test_saving_initialization(main_user, month):
    form = SavingPlanForm(user=main_user)

    assert month in form.fields

    assert isinstance(form.fields["journal"].widget, HiddenInput)
    assert form.fields["journal"].initial == main_user.journal


@time_machine.travel("1999-01-01")
def test_saving_blank_data(main_user):
    form = SavingPlanForm(user=main_user, data={})

    assert not form.is_valid()
    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "saving_type" in form.errors


def test_saving_unique_together_validation(main_user):
    existing_plan = SavingPlanFactory(year=1999)

    form = SavingPlanForm(
        user=main_user,
        data={
            "year": existing_plan.year,
            "saving_type": existing_plan.saving_type.pk,
            "january": 666.00,
        },
    )

    assert not form.is_valid()

    expected_msg = _("%(year)s year already has %(title)s plan.") % {
        "year": existing_plan.year,
        "title": existing_plan.saving_type.title,
    }
    assert form.errors == {"__all__": [expected_msg]}


def test_saving_unique_together_validation_more_than_one(main_user):
    """Tests that uniqueness doesn't block valid distinct inputs."""
    SavingPlanFactory(
        year=1999,
        saving_type=SavingTypeFactory(title="First"),
        journal=main_user.journal,
    )

    new_type = SavingTypeFactory(title="Second")
    form = SavingPlanForm(
        user=main_user,
        data={
            "year": 1999,
            "saving_type": new_type.pk,
            "january": 15.00,
        },
    )

    assert form.is_valid()


def test_saving_negative_number(main_user):
    type_ = SavingTypeFactory()

    data = {
        "year": 1999,
        "saving_type": type_.pk,
    }

    # Add a negative number to every single month
    for key, _ in month_names().items():
        data[key.lower()] = -1.00

    form = SavingPlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_saving_save_converts_to_cents(main_user):
    saving_type = SavingTypeFactory()

    form_data = {
        "year": 1999,
        "saving_type": saving_type.pk,
        "january": 0.01,
        "march": 2.5,
    }
    form = SavingPlanForm(data=form_data, user=main_user)

    assert form.is_valid()
    form.save()

    assert SavingPlan.objects.count() == 2

    jan_plan = SavingPlan.objects.get(month=1)
    mar_plan = SavingPlan.objects.get(month=3)

    assert jan_plan.price == 1
    assert jan_plan.year == 1999
    assert jan_plan.saving_type == saving_type

    assert mar_plan.price == 250
    assert mar_plan.year == 1999
    assert mar_plan.saving_type == saving_type


def test_saving_loads_initial_and_converts_from_cents(main_user):
    saving_type = SavingTypeFactory()
    plan_jan = SavingPlanFactory(month=1, price=15_000, saving_type=saving_type)
    SavingPlanFactory(month=12, price=30_000, saving_type=saving_type)

    form = SavingPlanForm(instance=plan_jan, user=main_user)

    assert form.initial["year"] == 1999
    assert form.initial["saving_type"] == saving_type.pk

    # 4. Assert conversion to standard floats for the frontend
    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert form.initial.get("february") is None

    # 5. Assert grouping fields are locked to prevent orphaned rows
    assert form.fields["year"].disabled is True
    assert form.fields["saving_type"].disabled is True


def test_saving_updates_and_deletes_rows(main_user):
    """Tests updates, deletions, and cents conversions handle correctly."""

    saving_type = SavingTypeFactory()

    plan_jan = SavingPlan.objects.create(
        year=2026,
        month=1,
        price=10000,
        saving_type=saving_type,
        journal=main_user.journal,
    )
    SavingPlan.objects.create(
        year=2026,
        month=2,
        price=20000,
        saving_type=saving_type,
        journal=main_user.journal,
    )

    updated_data = {
        "year": 2026,
        "saving_type": saving_type.pk,
        "january": 150.00,  # Updated
        "february": "",  # Cleared -> Should Delete
        "march": 300.00,  # New -> Should Create
    }

    form = SavingPlanForm(data=updated_data, instance=plan_jan, user=main_user)
    assert form.is_valid()
    form.save()

    # 3. Assert correct DB state in CENTS
    assert SavingPlan.objects.count() == 2
    assert SavingPlan.objects.filter(month=2).exists() is False
    assert SavingPlan.objects.get(month=1).price == 15000  # Updated to 15000
    assert SavingPlan.objects.get(month=3).price == 30000  # Created as 30000


def test_saving_plan_form_prevents_cross_category_pollution(main_user):
    salary_type = SavingTypeFactory(title="Salary", journal=main_user.journal)
    gift_type = SavingTypeFactory(title="Gift", journal=main_user.journal)

    # Create a Salary plan for Jan (Target instance)
    salary_instance = SavingPlanFactory(
        year=2026,
        month=1,
        price=100000,
        saving_type=salary_type,
        journal=main_user.journal,
    )

    # Create a Gift plan for Feb (Noise)
    SavingPlanFactory(
        year=2026,
        month=2,
        price=50000,
        saving_type=gift_type,
        journal=main_user.journal,
    )

    form = SavingPlanForm(user=main_user, instance=salary_instance)

    assert form.initial["january"] == 1000.0  # 100000 cents -> 1000.0 float
    assert form.initial.get("february") is None, "Cross-category pollution detected!"


# -------------------------------------------------------------------------------------
#                                                                   Necessary Plan Form
# -------------------------------------------------------------------------------------


def test_necessary_does_not_render_user_select(main_user):
    form = NecessaryPlanForm(user=main_user)
    rendered_html = form.as_p()

    assert '<select name="user"' not in rendered_html
    assert 'name="user"' not in rendered_html


@pytest.mark.parametrize("month", MONTHS)
def test_necessary_initialization(main_user, month):
    form = NecessaryPlanForm(user=main_user)

    assert month in form.fields

    assert isinstance(form.fields["journal"].widget, HiddenInput)
    assert form.fields["journal"].initial == main_user.journal


@time_machine.travel("1999-01-01")
def test_necessary_blank_data(main_user):
    form = NecessaryPlanForm(user=main_user, data={})

    assert not form.is_valid()
    assert len(form.errors) == 3
    assert "year" in form.errors
    assert "expense_type" in form.errors
    assert "title" in form.errors


def test_necessary_form_title_valid(
    main_user,
):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": "Car Insurance-2026_A",
        "expense_type": expense_type.pk,
        "january": 100.50,
        "year": 1999,
    }

    form = NecessaryPlanForm(data=data, user=main_user)

    assert form.is_valid(), f"Form should be valid, but got errors: {form.errors}"


def test_necessary_form_title_too_short(main_user):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": "ab",  # Only 2 characters
        "expense_type": expense_type.pk,
        "year": 1999,
        "january": 100.50,
    }

    form = NecessaryPlanForm(data=data, user=main_user)

    assert not form.is_valid()
    assert "title" in form.errors

    assert (
        "Įsitikinkite, kad reikšmė sudaryta iš nemažiau kaip 3 ženklų (dabartinis ilgis 2)."
        in form.errors["title"][0]
    )


def test_necessary_form_title_too_long(main_user):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": "a" * 101,  # 101 characters
        "expense_type": expense_type.pk,
        "year": 1999,
        "january": 100.50,
    }

    form = NecessaryPlanForm(data=data, user=main_user)

    assert not form.is_valid()
    assert "title" in form.errors
    assert (
        "Įsitikinkite, kad reikšmė sudaryta iš nedaugiau kaip 100 ženklų (dabartinis ilgis 101)."
        in form.errors["title"][0]
    )


@pytest.mark.parametrize(
    "title",
    [
        "Drop * table",
        "My@Plan",
        "<script>alert('x')</script>",
        "Insurance/Home",
    ],
)
def test_necessary_form_title_invalid_characters(main_user, title):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": title,
        "expense_type": expense_type.pk,
        "year": 1999,
        "january": 100.50,
    }

    form = NecessaryPlanForm(data=data, user=main_user)

    assert not form.is_valid()
    assert "title" in form.errors

    assert (
        _("Title can only contain letters, numbers, spaces, hyphens, and underscores.")
        in form.errors["title"][0]
    )


def test_necessary_unique_together_validation(main_user):
    existing_plan = NecessaryPlanFactory()

    form = NecessaryPlanForm(
        user=main_user,
        data={
            "year": existing_plan.year,
            "expense_type": existing_plan.expense_type.pk,
            "title": existing_plan.title,
            "january": 666.00,
        },
    )

    assert not form.is_valid()

    expected_msg = _("%(year)s year already has %(title)s plan.") % {
        "year": existing_plan.year,
        "title": existing_plan.expense_type.title,
    }
    assert form.errors == {"__all__": [expected_msg]}


def test_necessary_unique_together_validation_more_than_one(main_user):
    """Tests that uniqueness doesn't block valid distinct inputs."""
    NecessaryPlanFactory(
        year=1999,
        expense_type=ExpenseTypeFactory(title="First"),
        title="ABCD",
        journal=main_user.journal,
    )

    new_type = ExpenseTypeFactory(title="Second")
    form = NecessaryPlanForm(
        user=main_user,
        data={
            "year": 1999,
            "expense_type": new_type.pk,
            "title": "ABCD",
            "january": 15.00,
        },
    )

    assert form.is_valid()


def test_necessary_negative_number(main_user):
    expense_type = ExpenseTypeFactory()

    data = {
        "year": 1999,
        "expense_type": expense_type.pk,
        "title": "ABCD",
    }

    # Add a negative number to every single month
    for key, _ in month_names().items():
        data[key.lower()] = -1.00

    form = NecessaryPlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_necessary_save_converts_to_cents(main_user):
    expense_type = ExpenseTypeFactory()

    form_data = {
        "year": 1999,
        "expense_type": expense_type.pk,
        "title": "XXX",
        "january": 0.01,
        "march": 2.5,
    }
    form = NecessaryPlanForm(data=form_data, user=main_user)

    assert form.is_valid()
    form.save()

    assert NecessaryPlan.objects.count() == 2

    jan_plan = NecessaryPlan.objects.get(month=1)
    mar_plan = NecessaryPlan.objects.get(month=3)

    assert jan_plan.price == 1
    assert jan_plan.year == 1999
    assert jan_plan.expense_type == expense_type
    assert jan_plan.title == "XXX"

    assert mar_plan.price == 250
    assert mar_plan.year == 1999
    assert mar_plan.expense_type == expense_type
    assert mar_plan.title == "XXX"


def test_necessary_loads_initial_and_converts_from_cents(main_user):
    title = "X"
    expense_type = ExpenseTypeFactory()
    plan_jan = NecessaryPlanFactory(
        month=1, price=15_000, expense_type=expense_type, title=title
    )
    NecessaryPlanFactory(month=12, price=30_000, expense_type=expense_type, title=title)

    form = NecessaryPlanForm(instance=plan_jan, user=main_user)

    assert form.initial["year"] == 1999
    assert form.initial["expense_type"] == expense_type.pk
    assert form.initial["title"] == title

    # 4. Assert conversion to standard floats for the frontend
    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert form.initial.get("february") is None

    # 5. Assert grouping fields are locked to prevent orphaned rows
    assert form.fields["year"].disabled is True
    assert form.fields["expense_type"].disabled is True
    assert form.fields["title"].disabled is True


def test_necessary_updates_and_deletes_rows(main_user):
    """Tests updates, deletions, and cents conversions handle correctly."""

    title = "Xxx"
    expense_type = ExpenseTypeFactory()

    plan_jan = NecessaryPlan.objects.create(
        year=2026,
        month=1,
        price=10000,
        expense_type=expense_type,
        title=title,
        journal=main_user.journal,
    )
    NecessaryPlan.objects.create(
        year=2026,
        month=2,
        price=20000,
        expense_type=expense_type,
        title=title,
        journal=main_user.journal,
    )

    updated_data = {
        "year": 2026,
        "expense_type": expense_type.pk,
        "title": title,
        "january": 150.00,  # Updated
        "february": "",  # Cleared -> Should Delete
        "march": 300.00,  # New -> Should Create
    }

    form = NecessaryPlanForm(data=updated_data, instance=plan_jan, user=main_user)
    assert form.is_valid()
    form.save()

    # 3. Assert correct DB state in CENTS
    assert NecessaryPlan.objects.count() == 2
    assert NecessaryPlan.objects.filter(month=2).exists() is False
    assert NecessaryPlan.objects.get(month=1).price == 15000  # Updated to 15000
    assert NecessaryPlan.objects.get(month=3).price == 30000  # Created as 30000


def test_necessary_plan_form_prevents_cross_category_pollution(main_user):
    e1 = ExpenseTypeFactory(title="E1", journal=main_user.journal)
    e2 = ExpenseTypeFactory(title="E2", journal=main_user.journal)

    e1_instance = NecessaryPlanFactory(
        year=2026,
        month=1,
        price=100000,
        expense_type=e1,
        title="X",
        journal=main_user.journal,
    )

    NecessaryPlanFactory(
        year=2026,
        month=2,
        price=50000,
        expense_type=e2,
        title="X",
        journal=main_user.journal,
    )

    form = NecessaryPlanForm(user=main_user, instance=e1_instance)

    assert form.initial["january"] == 1000.0  # 100000 cents -> 1000.0 float
    assert form.initial.get("february") is None, "Cross-category pollution detected!"


# -------------------------------------------------------------------------------------
#                                                                         Day Plan Form
# -------------------------------------------------------------------------------------


def test_day_does_not_render_user_select(main_user):
    form = DayPlanForm(user=main_user)
    rendered_html = form.as_p()

    assert '<select name="user"' not in rendered_html
    assert 'name="user"' not in rendered_html


@pytest.mark.parametrize("month", MONTHS)
def test_day_initialization(main_user, month):
    form = DayPlanForm(user=main_user)

    assert month in form.fields

    assert isinstance(form.fields["journal"].widget, HiddenInput)
    assert form.fields["journal"].initial == main_user.journal


@time_machine.travel("1999-01-01")
def test_day_blank_data(main_user):
    form = DayPlanForm(user=main_user, data={})

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert "year" in form.errors


def test_day_unique_together_validation_more_than_one(main_user):
    """Tests that uniqueness doesn't block valid distinct inputs."""
    existing_plan = DayPlanFactory(
        year=1999,
        journal=main_user.journal,
    )

    form = DayPlanForm(
        user=main_user,
        data={
            "year": 1999,
            "january": 15.00,
        },
    )

    assert not form.is_valid()
    expected_msg = _("Plan for %(year)s already exists.") % {
        "year": existing_plan.year,
    }
    assert form.errors == {"__all__": [expected_msg]}


def test_day_negative_number(main_user):
    data = {
        "year": 1999,
    }

    # Add a negative number to every single month
    for key, _ in month_names().items():
        data[key.lower()] = -1.00

    form = DayPlanForm(user=main_user, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_day_save_converts_to_cents(main_user):
    form_data = {
        "year": 1999,
        "january": 0.01,
        "march": 2.5,
    }
    form = DayPlanForm(data=form_data, user=main_user)

    assert form.is_valid()
    form.save()

    assert DayPlan.objects.count() == 2

    jan_plan = DayPlan.objects.get(month=1)
    mar_plan = DayPlan.objects.get(month=3)

    assert jan_plan.price == 1
    assert jan_plan.year == 1999

    assert mar_plan.price == 250
    assert mar_plan.year == 1999


def test_day_loads_initial_and_converts_from_cents(main_user):
    plan_jan = DayPlanFactory(month=1, price=15_000)
    DayPlanFactory(month=12, price=30_000)

    form = DayPlanForm(instance=plan_jan, user=main_user)

    assert form.initial["year"] == 1999

    # 4. Assert conversion to standard floats for the frontend
    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert form.initial.get("february") is None

    # 5. Assert grouping fields are locked to prevent orphaned rows
    assert form.fields["year"].disabled is True


def test_day_updates_and_deletes_rows(main_user):
    """Tests updates, deletions, and cents conversions handle correctly."""

    plan_jan = DayPlan.objects.create(
        year=2026,
        month=1,
        price=10000,
        journal=main_user.journal,
    )
    DayPlan.objects.create(
        year=2026,
        month=2,
        price=20000,
        journal=main_user.journal,
    )

    updated_data = {
        "year": 2026,
        "january": 150.00,  # Updated
        "february": "",  # Cleared -> Should Delete
        "march": 300.00,  # New -> Should Create
    }

    form = DayPlanForm(data=updated_data, instance=plan_jan, user=main_user)
    assert form.is_valid()
    form.save()

    # 3. Assert correct DB state in CENTS
    assert DayPlan.objects.count() == 2
    assert DayPlan.objects.filter(month=2).exists() is False
    assert DayPlan.objects.get(month=1).price == 15000  # Updated to 15000
    assert DayPlan.objects.get(month=3).price == 30000  # Created as 30000


# -------------------------------------------------------------------------------------
#                                                                       Copy Plans Form
# -------------------------------------------------------------------------------------


def test_copy_init(main_user):
    form = CopyPlanForm(user=main_user)
    assert form.fields["year_from"].initial == datetime.now().year
    assert form.fields["income"].initial is True


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
    # Setup
    IncomePlanFactory(year=1999, journal=main_user.journal)
    IncomePlanFactory(year=2000, journal=main_user.journal)

    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert not form.is_valid()
    assert form.errors == {"income": ["2000 metai jau turi planus."]}


def test_copy_to_table_have_records_from_empty(main_user):
    IncomePlanFactory(year=2000, journal=main_user.journal)

    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert not form.is_valid()
    assert form.errors == {
        "income": ["Nėra ką kopijuoti.", "2000 metai jau turi planus."]
    }


def test_copy_data(main_user):
    income_type = IncomeTypeFactory(journal=main_user.journal)

    # User has plans for Jan and March in 1999
    IncomePlanFactory(
        year=1999,
        month=1,
        price=100,
        income_type=income_type,
        journal=main_user.journal,
    )
    IncomePlanFactory(
        year=1999,
        month=3,
        price=300,
        income_type=income_type,
        journal=main_user.journal,
    )

    form = CopyPlanForm(
        user=main_user, data={"year_from": 1999, "year_to": 2000, "income": True}
    )

    assert form.is_valid()
    form.save()

    # Verify 2000 has exactly two tall rows
    copied_data = IncomePlanModelService(main_user).year(2000)

    assert copied_data.count() == 2
    assert copied_data.get(month=1).price == 100
    assert copied_data.get(month=3).price == 300
