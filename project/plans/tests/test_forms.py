import pytest
import time_machine
from django.forms import HiddenInput
from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ..forms import (
    DayPlanForm,
    ExpensePlanForm,
    IncomePlanForm,
    NecessaryPlanForm,
    SavingPlanForm,
)
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