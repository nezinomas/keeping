import pytest
from freezegun import freeze_time

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from ..forms import (CopyPlanForm, DayPlanForm, ExpensePlanForm,
                     IncomePlanForm, NecessaryPlanForm, SavingPlanForm)


# ----------------------------------------------------------------------------
#                                                               Necessary Form
# ----------------------------------------------------------------------------
def test_necessary_init():
    NecessaryPlanForm()


@pytest.mark.django_db
def test_necessary_valid_data():
    form = NecessaryPlanForm(data={
        'year': 1999,
        'title': 'X',
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.title == 'X'
    assert data.january == 15.0
    assert not data.february


@freeze_time('1999-01-01')
def test_necessary_blank_data():
    form = NecessaryPlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year': ['Šis laukas yra privalomas.'],
        'title': ['Šis laukas yra privalomas.'],
    }


# ----------------------------------------------------------------------------
#                                                                     Day Form
# ----------------------------------------------------------------------------
def test_day_init():
    DayPlanForm()


@pytest.mark.django_db
def test_day_valid_data():
    form = DayPlanForm(data={
        'year': 1999,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert not data.february


@freeze_time('1999-01-01')
def test_day_blank_data():
    form = DayPlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year': ['Šis laukas yra privalomas.'],
    }


# ----------------------------------------------------------------------------
#                                                                  Saving Form
# ----------------------------------------------------------------------------
def test_saving_init():
    SavingPlanForm()


@pytest.mark.django_db
def test_saving_valid_data():
    type_ = SavingTypeFactory()
    form = SavingPlanForm(data={
        'year': 1999,
        'saving_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert str(data.saving_type) == 'Savings'
    assert not data.february


@freeze_time('1999-01-01')
def test_saving_blank_data():
    form = SavingPlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year': ['Šis laukas yra privalomas.'],
        'saving_type': ['Šis laukas yra privalomas.'],
    }


@pytest.mark.django_db
def test_saving_form_type_closed_in_past():
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingPlanForm(data={}, year=3000)

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


@pytest.mark.django_db
def test_saving_form_type_closed_in_future():
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingPlanForm(data={}, year=1000)

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


@pytest.mark.django_db
def test_saving_form_type_closed_in_current_year():
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingPlanForm(data={}, year=2000)

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


# ----------------------------------------------------------------------------
#                                                                  Income Form
# ----------------------------------------------------------------------------
def test_income_init():
    IncomePlanForm()


@pytest.mark.django_db
def test_income_valid_data():
    type_ = IncomeTypeFactory()
    form = IncomePlanForm(data={
        'year': 1999,
        'income_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert str(data.income_type) == 'Income Type'
    assert not data.february


@freeze_time('1999-01-01')
def test_income_blank_data():
    form = IncomePlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year': ['Šis laukas yra privalomas.'],
        'income_type': ['Šis laukas yra privalomas.'],
    }


# ----------------------------------------------------------------------------
#                                                                 Expense Form
# ----------------------------------------------------------------------------
def test_expense_init():
    ExpensePlanForm()


@pytest.mark.django_db
def test_expense_valid_data():
    type_ = ExpenseTypeFactory()
    form = ExpensePlanForm(data={
        'year': 1999,
        'expense_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert str(data.expense_type) == 'Expense Type'
    assert not data.february


@freeze_time('1999-01-01')
def test_expense_blank_data():
    form = ExpensePlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year': ['Šis laukas yra privalomas.'],
        'expense_type': ['Šis laukas yra privalomas.'],
    }


# ----------------------------------------------------------------------------
#                                                                    Copy Form
# ----------------------------------------------------------------------------
def test_copy_init():
    CopyPlanForm()


def test_copy_have_fields():
    form = CopyPlanForm().as_p()

    assert '<input type="text" name="year_from"' in form
    assert '<input type="text" name="year_to"' in form
    assert '<input type="checkbox" name="income"' in form
    assert '<input type="checkbox" name="expense"' in form
    assert '<input type="checkbox" name="saving"' in form
    assert '<input type="checkbox" name="day"' in form
    assert '<input type="checkbox" name="necessary"' in form


def test_copy_blank_data():
    form = CopyPlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year_from': ['Šis laukas yra privalomas.'],
        'year_to': ['Šis laukas yra privalomas.'],
    }


def test_copy_all_checkboxes_unselected():
    form = CopyPlanForm(data={
        'year_from': 1999,
        'year_to': 2000,
    })

    assert not form.is_valid()

    assert form.errors == {
        '__all__': ['Reikia pažymėti nors vieną planą.']
    }


@pytest.mark.django_db
def test_copy_empty_from_tables():
    form = CopyPlanForm(data={
        'year_from': 1999,
        'year_to': 2000,
        'income': True
    })

    assert not form.is_valid()

    assert form.errors == {
        'income': ['Nėra ką kopijuoti.']
    }
