import pytest
from freezegun import freeze_time

from ...core.lib.transalation import month_names
from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from ...users.factories import UserFactory
from ..factories import (DayPlanFactory, ExpensePlanFactory, IncomePlanFactory,
                         NecessaryPlanFactory, SavingPlanFactory)
from ..forms import (CopyPlanForm, DayPlanForm, ExpensePlanForm,
                     IncomePlanForm, NecessaryPlanForm, SavingPlanForm)
from ..models import IncomePlan

pytestmark = pytest.mark.django_db

# ----------------------------------------------------------------------------
#                                                                  Income Form
# ----------------------------------------------------------------------------
def test_income_init():
    IncomePlanForm()


def test_income_init_fields():
    form = IncomePlanForm().as_p()

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


@freeze_time('1000-01-01')
def test_income_year_initial_value():
    UserFactory()

    form = IncomePlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_income_current_user_types(second_user):
    IncomeTypeFactory(title='T1')  # user bob, current user
    IncomeTypeFactory(title='T2', journal=second_user.journal)  # user X

    form = IncomePlanForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_income_valid_data():
    type_ = IncomeTypeFactory()
    form = IncomePlanForm({
        'year': 1999,
        'income_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert str(data.income_type) == 'Income Type'
    assert data.journal.users.first().username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_income_blank_data():
    form = IncomePlanForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'income_type' in form.errors


def test_income_unique_together_validation():
    i = IncomePlanFactory()

    form = IncomePlanForm({
        'year': i.year,
        'income_type': i.income_type.pk,
        'january': 666,
    })

    assert not form.is_valid()

    assert form.errors == {
        '__all__': ['1999 metai jau turi Income Type planą.']
    }


def test_income_unique_together_validation_more_than_one():
    IncomePlanFactory(income_type=IncomeTypeFactory(title='First'))

    type_ = IncomeTypeFactory()
    form = IncomePlanForm({
        'year': 1999,
        'income_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()


def test_income_negative_number():
    IncomePlanFactory(income_type=IncomeTypeFactory(title='First'))

    type_ = IncomeTypeFactory()

    data = {
        'year': 1999,
        'income_type': type_.pk,
    }

    # add negative numbet to earch month
    for key, _ in month_names().items():
        data[key.lower()] = -0.01

    form = IncomePlanForm(data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


def test_income_inputs_as_string():
    IncomePlanFactory(income_type=IncomeTypeFactory(title='First'))

    type_ = IncomeTypeFactory()

    data = {
        'year': 1999,
        'income_type': type_.pk,
    }

    # add negative numbet to earch month
    for key, _ in month_names().items():
        data[key.lower()] = 'a'

    form = IncomePlanForm(data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


# ----------------------------------------------------------------------------
#                                                                 Expense Form
# ----------------------------------------------------------------------------
def test_expense_init():
    ExpensePlanForm()


def test_expense_init_fields():
    form = ExpensePlanForm().as_p()

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

@freeze_time('1000-01-01')
def test_expense_year_initial_value():
    UserFactory()

    form = ExpensePlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_expense_current_user_types(second_user):
    ExpenseTypeFactory(title='T1')  # user bob, current user
    ExpenseTypeFactory(title='T2', journal=second_user.journal)  # user X

    form = ExpensePlanForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_expense_valid_data():
    type_ = ExpenseTypeFactory()
    form = ExpensePlanForm({
        'year': 1999,
        'expense_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert str(data.expense_type) == 'Expense Type'
    assert data.journal.users.first().username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_expense_blank_data():
    form = ExpensePlanForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'expense_type' in form.errors


def test_expense_unique_together_validation():
    i = ExpensePlanFactory()

    form = ExpensePlanForm({
        'year': i.year,
        'expense_type': i.expense_type.pk,
        'january': 666,
    })

    assert not form.is_valid()

    assert form.errors == {
        '__all__': ['1999 metai jau turi Expense Type planą.']
    }


def test_expense_unique_together_validation_more_than_one():
    ExpensePlanFactory(expense_type=ExpenseTypeFactory(title='First'))
    t = ExpenseTypeFactory()
    form = ExpensePlanForm({
        'year': 1999,
        'expense_type': t.pk,
        'january': 15.0,
    })

    assert form.is_valid()


# ----------------------------------------------------------------------------
#                                                                  Saving Form
# ----------------------------------------------------------------------------
def test_saving_init():
    SavingPlanForm()


def test_saving_init_fields():
    form = SavingPlanForm().as_p()

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


@freeze_time('1000-01-01')
def test_saving_year_initial_value():
    UserFactory()

    form = SavingPlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_saving_current_user_types(second_user):
    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', journal=second_user.journal)  # user X

    form = SavingPlanForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_saving_valid_data():
    type_ = SavingTypeFactory()
    form = SavingPlanForm({
        'year': 1999,
        'saving_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert str(data.saving_type) == 'Savings'
    assert data.journal.users.first().username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_saving_blank_data():
    form = SavingPlanForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'saving_type' in form.errors


def test_saving_unique_together_validation():
    i = SavingPlanFactory()

    form = SavingPlanForm({
        'year': i.year,
        'saving_type': i.saving_type.pk,
        'january': 666,
    })

    assert not form.is_valid()

    assert form.errors == {
        '__all__': ['1999 metai jau turi Savings planą.']
    }


def test_saving_unique_together_validation_more_than_on():
    SavingPlanFactory(saving_type=SavingTypeFactory(title='First'))

    t = SavingTypeFactory()
    form = SavingPlanForm({
        'year': 1999,
        'saving_type': t.pk,
        'january': 15.0,
    })


    assert form.is_valid()


def test_saving_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingPlanForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


def test_saving_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingPlanForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_saving_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingPlanForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


# ----------------------------------------------------------------------------
#                                                                     Day Form
# ----------------------------------------------------------------------------
def test_day_init():
    DayPlanForm()


def test_day_init_fields():
    form = DayPlanForm().as_p()

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


@freeze_time('1000-01-01')
def test_day_year_initial_value():
    UserFactory()

    form = DayPlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_day_valid_data():
    form = DayPlanForm({
        'year': 1999,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert data.journal.users.first().username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_day_blank_data():
    form = DayPlanForm({})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'year' in form.errors



def test_day_unique_together_validation():
    i = DayPlanFactory()

    form = DayPlanForm({
        'year': i.year,
        'january': 666,
    })

    assert not form.is_valid()

    assert form.errors == {
        '__all__': ['1999 metai jau turi Dienos planą.']
    }


# ----------------------------------------------------------------------------
#                                                               Necessary Form
# ----------------------------------------------------------------------------
def test_necessary_init():
    NecessaryPlanForm()


def test_necessary_init_fields():
    form = NecessaryPlanForm().as_p()

    assert '<input type="text" name="year"' in form
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


@freeze_time('1000-01-01')
def test_income_year_initial_value1():
    UserFactory()

    form = NecessaryPlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_necessary_valid_data():
    form = NecessaryPlanForm({
        'year': 1999,
        'title': 'XXX',
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert data.title == 'XXX'
    assert data.journal.users.first().username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_necessary_blank_data():
    form = NecessaryPlanForm({})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'title' in form.errors


def test_necessary_unique_together_validation():
    i = NecessaryPlanFactory(title='XXX')

    form = NecessaryPlanForm({
        'year': i.year,
        'title': i.title,
        'january': 666,
    })

    assert not form.is_valid()

    assert form.errors == {
        '__all__': ['1999 metai jau turi XXX planą.']
    }


def test_necessary_unique_together_validation_more_than_one():
    NecessaryPlanFactory(title='First')

    form = NecessaryPlanForm({
        'year': 1999,
        'title': 'XXX',
        'january': 15.0,
    })

    assert form.is_valid()


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
        '__all__': ['Reikia pažymėti nors vieną planą.'],
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


def test_copy_to_table_have_records():
    IncomePlanFactory(year=1999)
    IncomePlanFactory(year=2000)

    form = CopyPlanForm(data={
        'year_from': 1999,
        'year_to': 2000,
        'income': True
    })

    assert not form.is_valid()

    assert form.errors == {
        'income': ['2000 metai jau turi planus.']
    }


def test_copy_to_table_have_records_from_empty():
    IncomePlanFactory(year=2000)

    form = CopyPlanForm(data={
        'year_from': 1999,
        'year_to': 2000,
        'income': True
    })

    assert not form.is_valid()

    assert form.errors == {
        'income': [
            'Nėra ką kopijuoti.',
            '2000 metai jau turi planus.'
        ]
    }


def test_copy_data():
    IncomePlanFactory(year=1999)

    form = CopyPlanForm(data={
        'year_from': 1999,
        'year_to': 2000,
        'income': True
    })

    assert form.is_valid()

    form.save()

    data = IncomePlan.objects.year(2000)

    assert data.exists()
    assert data[0].year == 2000
