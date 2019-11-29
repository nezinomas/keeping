import pytest
from freezegun import freeze_time

from ...users.factories import UserFactory
from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from ..factories import (
    DayPlanFactory, ExpensePlanFactory, IncomePlanFactory,
    NecessaryPlanFactory, SavingPlanFactory)
from ..forms import (CopyPlanForm, DayPlanForm, ExpensePlanForm,
                     IncomePlanForm, NecessaryPlanForm, SavingPlanForm)
from ..models import IncomePlan

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Income Form
# ----------------------------------------------------------------------------
def test_income_init(get_user):
    IncomePlanForm()


def test_income_init_fields(get_user):
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
def test_income_year_initial_value(get_user):
    UserFactory()

    form = IncomePlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_income_current_user_types(get_user):
    u = UserFactory(username='tom')

    IncomeTypeFactory(title='T1')  # user bob, current user
    IncomeTypeFactory(title='T2', user=u)  # user tom

    form = IncomePlanForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_income_valid_data(get_user):
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
    assert data.user.username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_income_blank_data(get_user):
    form = IncomePlanForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'income_type' in form.errors


def test_income_unique_together_validation(get_user):
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


def test_income_unique_together_validation_more_than_one(get_user):
    IncomePlanFactory(income_type=IncomeTypeFactory(title='First'))

    type_ = IncomeTypeFactory()
    form = IncomePlanForm({
        'year': 1999,
        'income_type': type_.pk,
        'january': 15.0,
    })

    assert form.is_valid()



# ----------------------------------------------------------------------------
#                                                                 Expense Form
# ----------------------------------------------------------------------------
def test_expense_init(get_user):
    ExpensePlanForm()


def test_expense_init_fields(get_user):
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
def test_expense_year_initial_value(get_user):
    UserFactory()

    form = ExpensePlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_expense_current_user_types(get_user):
    u = UserFactory(username='tom')

    ExpenseTypeFactory(title='T1')  # user bob, current user
    ExpenseTypeFactory(title='T2', user=u)  # user tom

    form = ExpensePlanForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_expense_valid_data(get_user):
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
    assert data.user.username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_expense_blank_data(get_user):
    form = ExpensePlanForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'expense_type' in form.errors


def test_expense_unique_together_validation(get_user):
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


def test_expense_unique_together_validation_more_than_one(get_user):
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
def test_saving_init(get_user):
    SavingPlanForm()


def test_saving_init_fields(get_user):
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
def test_saving_year_initial_value(get_user):
    UserFactory()

    form = SavingPlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_saving_current_user_types(get_user):
    u = UserFactory(username='tom')

    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', user=u)  # user tom

    form = SavingPlanForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_saving_valid_data(get_user):
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
    assert data.user.username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_saving_blank_data(get_user):
    form = SavingPlanForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'saving_type' in form.errors


def test_saving_unique_together_validation(get_user):
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


def test_saving_unique_together_validation_more_than_on(get_user):
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
def test_day_init(get_user):
    DayPlanForm()


def test_day_init_fields(get_user):
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
def test_day_year_initial_value(get_user):
    UserFactory()

    form = DayPlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_day_valid_data(get_user):
    form = DayPlanForm({
        'year': 1999,
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.january == 15.0
    assert data.user.username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_day_blank_data(get_user):
    form = DayPlanForm({})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'year' in form.errors



def test_day_unique_together_validation(get_user):
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
def test_necessary_init(get_user):
    NecessaryPlanForm()


def test_necessary_init_fields(get_user):
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
def test_income_year_initial_value(get_user):
    UserFactory()

    form = NecessaryPlanForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_necessary_valid_data(get_user):
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
    assert data.user.username == 'bob'
    assert not data.february


@freeze_time('1999-01-01')
def test_necessary_blank_data(get_user):
    form = NecessaryPlanForm({})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'title' in form.errors


def test_necessary_unique_together_validation(get_user):
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


def test_necessary_unique_together_validation_more_than_one(get_user):
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


def test_copy_empty_from_tables(get_user):
    form = CopyPlanForm(data={
        'year_from': 1999,
        'year_to': 2000,
        'income': True
    })

    assert not form.is_valid()

    assert form.errors == {
        'income': ['Nėra ką kopijuoti.']
    }


def test_copy_to_table_have_records(get_user):
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


def test_copy_to_table_have_records_from_empty(get_user):
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


def test_copy_data(get_user):
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
