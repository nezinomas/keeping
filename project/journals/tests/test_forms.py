import json

import pytest

from ...expenses.factories import ExpenseTypeFactory
from ...journals.factories import JournalFactory
from ...journals.models import Journal
from ..forms import UnnecessaryForm

pytestmark = pytest.mark.django_db


def test_form_init():
    UnnecessaryForm()


def test_form_fields():
    ExpenseTypeFactory(title='X')
    ExpenseTypeFactory(title='Y')
    form = UnnecessaryForm().as_p()

    assert form.count('<input type="checkbox"') == 3


def test_form_selected_expenses(get_user):
    e1 = ExpenseTypeFactory(title='X')
    e2 = ExpenseTypeFactory(title='Y')

    get_user.journal.unnecessary_expenses = json.dumps([e1.pk, e2.pk])
    get_user.journal.save()

    form = UnnecessaryForm().as_p()

    assert form.count('checked') == 2


def test_form_bad_json_for_expenses(get_user):
    e1 = ExpenseTypeFactory(title='X')
    e2 = ExpenseTypeFactory(title='Y')

    get_user.journal.unnecessary_expenses = 'None'
    get_user.journal.save()

    form = UnnecessaryForm().as_p()

    assert form.count('checked') == 0


def test_form_selected_savings(get_user):
    get_user.journal.unnecessary_savings = True
    get_user.journal.save()

    form = UnnecessaryForm().as_p()

    assert form.count('checked') == 1


def test_form_save_checked_all():
    e1 = ExpenseTypeFactory(title='X')
    e2 = ExpenseTypeFactory(title='Y')
    form = UnnecessaryForm(data={
        'savings': True,
        'choices': {e1.pk: True, e2: True}
    })

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == '[1, 2]'
    assert actual.unnecessary_savings


def test_form_save_checked_none():
    ExpenseTypeFactory(title='X')
    ExpenseTypeFactory(title='Y')
    form = UnnecessaryForm(data={
        'savings': False,
        'choices': {}
    })

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()
    assert not actual.unnecessary_expenses
    assert not actual.unnecessary_savings


def test_form_save_unchecked_expenses(get_user):
    e1 = ExpenseTypeFactory(title='X')

    get_user.journal.unnecessary_expenses = json.dumps([e1.pk])
    get_user.journal.save()

    form = UnnecessaryForm(data={
        'savings': False,
        'choices': {}
    })

    assert form.is_valid()

    form.save()

    actual = Journal.objects.first()
    assert not actual.unnecessary_expenses
    assert not actual.unnecessary_savings
