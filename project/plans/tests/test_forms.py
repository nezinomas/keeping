import pytest
from freezegun import freeze_time

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from ..forms import (DayPlanForm, ExpensePlanForm, IncomePlanForm,
                     NecessaryPlanForm, SavingPlanForm)


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
