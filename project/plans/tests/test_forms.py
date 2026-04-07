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
from ..models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan
from ..tests.factories import (
    ExpenseTypeFactory,
    IncomePlanFactory,
    IncomeTypeFactory,
    NecessaryPlanFactory,
    SavingTypeFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def income_type():
    """Creates a default IncomeType for the tests."""
    return IncomeTypeFactory()


@pytest.fixture
def expense_type():
    """Creates a default ExpenseType for the tests."""
    return ExpenseTypeFactory()


@pytest.fixture
def saving_type():
    """Creates a default SavingType for the tests."""
    return SavingTypeFactory()


@pytest.fixture
def form_data(income_type):
    """Basic valid data for an IncomePlanForm using Euros/Cents format."""
    return {
        "year": 2026,
        "income_type": income_type.pk,
        "january": 100.50,
        "march": 250.00,
    }


def test_form_does_not_render_user_select(main_user):
    """Ensures the user field is never exposed in the HTML output."""
    form = IncomePlanForm(user=main_user)
    rendered_html = form.as_p()

    assert '<select name="user"' not in rendered_html
    assert 'name="user"' not in rendered_html


def test_form_initialization(main_user):
    """Tests that the form generates all 12 months and hides the journal securely."""
    form = IncomePlanForm(user=main_user)

    # Check 12 months exist
    assert "january" in form.fields
    assert "december" in form.fields

    # Check Journal is handled securely
    assert isinstance(form.fields["journal"].widget, HiddenInput)
    assert form.fields["journal"].initial == main_user.journal


@time_machine.travel("1999-01-01")
def test_income_blank_data(main_user):
    """Tests that year and income_type are strictly required."""
    form = IncomePlanForm(user=main_user, data={})

    assert not form.is_valid()
    assert len(form.errors) == 2
    assert "year" in form.errors
    assert "income_type" in form.errors


def test_income_unique_together_validation(main_user):
    """Tests that a user cannot create a duplicate plan (UniqueTogether enforcement)."""
    existing_plan = IncomePlanFactory(year=1999, journal=main_user.journal)

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
    """Tests that the MONTH_FIELD_KWARGS correctly blocks negative inputs."""
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


def test_form_save_converts_to_cents(main_user, form_data, income_type):
    """Tests that wide form floats (100.50) save as tall DB integers (10050)."""
    form = IncomePlanForm(data=form_data, user=main_user)

    assert form.is_valid()
    form.save()

    # Sparse data check: Only 2 rows should exist!
    assert IncomePlan.objects.count() == 2

    jan_plan = IncomePlan.objects.get(month=1)
    mar_plan = IncomePlan.objects.get(month=3)

    assert jan_plan.price == 10050
    assert jan_plan.year == 2026
    assert jan_plan.income_type == income_type
    assert mar_plan.price == 25000


def test_form_loads_initial_and_converts_from_cents(main_user, income_type):
    """Tests that tall DB integers (15000) load into the form as floats (150.00)."""
    # 1. Create DB rows in CENTS
    plan_jan = IncomePlan.objects.create(
        year=2026,
        month=1,
        price=15000,
        income_type=income_type,
        journal=main_user.journal,
    )
    IncomePlan.objects.create(
        year=2026,
        month=12,
        price=30000,
        income_type=income_type,
        journal=main_user.journal,
    )

    # 2. Initialize the form with an instance
    form = IncomePlanForm(instance=plan_jan, user=main_user)

    # 3. Assert the form successfully converted tall rows to wide initial data
    assert form.initial["year"] == 2026
    assert form.initial["income_type"] == income_type.pk

    # 4. Assert conversion to standard floats for the frontend
    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert form.initial.get("february") is None

    # 5. Assert grouping fields are locked to prevent orphaned rows
    assert form.fields["year"].disabled is True
    assert form.fields["income_type"].disabled is True


def test_form_updates_and_deletes_rows(main_user, income_type):
    """Tests updates, deletions, and cents conversions handle correctly."""
    # 1. Setup existing DB state in CENTS (Jan=10000, Feb=20000)
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

    # 2. User submits modified data in EUROS
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


def test_day_plan_form_saves_without_grouping_fields(main_user):
    """DayPlan is unique because it only groups by year/journal, no extra FKs."""
    data = {
        "year": 2026,
        "january": 50.00,
        "june": 100.00,
    }

    form = DayPlanForm(data=data, user=main_user)
    assert form.is_valid()
    form.save()

    assert DayPlan.objects.count() == 2
    assert DayPlan.objects.get(month=1).price == 5000  # 50 euros -> 5000 cents
    assert DayPlan.objects.get(month=6).price == 10000


def test_necessary_plan_form_saves_with_multiple_grouping_fields(
    main_user, expense_type
):
    """Test: Proves the form correctly maps BOTH title and expense_type to the tall DB rows."""
    data = {
        "year": 2026,
        "title": "Car Insurance",
        "expense_type": expense_type.pk,
        "january": 500.00,
    }

    form = NecessaryPlanForm(data=data, user=main_user)

    assert form.is_valid(), form.errors
    form.save()

    # Assert exactly 1 row was created
    assert NecessaryPlan.objects.count() == 1

    plan = NecessaryPlan.objects.first()

    # Assert values and cents conversion
    assert plan.amount == 50000
    assert plan.year == 2026
    assert plan.month == 1
    assert plan.title == "Car Insurance"
    assert plan.expense_type == expense_type


def test_necessary_plan_custom_unique_validation(main_user, expense_type):
    """Test: Proves the custom get_duplicate_error_message override works perfectly."""
    # 1. Setup: Create an existing tall row in the database
    NecessaryPlanFactory(
        year=2026,
        month=1,
        title="Car Insurance",
        expense_type=expense_type,
        journal=main_user.journal,
    )

    # 2. User tries to submit the exact same Year + Title + Type combination
    data = {
        "year": 2026,
        "title": "Car Insurance",
        "expense_type": expense_type.pk,
        "february": 100.00,
    }
    form = NecessaryPlanForm(data=data, user=main_user)

    # 3. Assert it is caught by validation
    assert not form.is_valid()

    # 4. Assert the error message matches your custom override EXACTLY
    expected_msg = _("%(year)s year and %(type)s already has %(title)s plan.") % {
        "year": 2026,
        "title": "Car Insurance",
        "type": expense_type.title,
    }

    assert form.errors == {"__all__": [expected_msg]}


def test_expense_plan_form_wiring(main_user, expense_type):
    """Smoke test to ensure ExpensePlanForm is wired correctly."""
    data = {
        "year": 2026,
        "expense_type": expense_type.pk,
        "january": 100.00,
    }
    form = ExpensePlanForm(data=data, user=main_user)

    assert form.is_valid(), form.errors
    form.save()
    assert ExpensePlan.objects.count() == 1


def test_saving_plan_form_wiring(main_user, saving_type):
    """Smoke test to ensure SavingPlanForm is wired correctly."""
    data = {
        "year": 2026,
        "saving_type": saving_type.pk,
        "january": 100.00,
    }
    form = SavingPlanForm(data=data, user=main_user)

    assert form.is_valid(), form.errors
    form.save()
    assert SavingPlan.objects.count() == 1
