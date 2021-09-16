from datetime import date
from decimal import Decimal
from io import BytesIO

import mock
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from freezegun import freeze_time
from PIL import Image

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from ..factories import ExpenseNameFactory, ExpenseTypeFactory
from ..forms import ExpenseForm, ExpenseNameForm, ExpenseTypeForm

pytestmark = pytest.mark.django_db

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)

# ----------------------------------------------------------------------------
#                                                                      Expense
# ----------------------------------------------------------------------------
def test_expense_form_init():
    ExpenseForm(data={})


def test_expense_init_fields():
    form = ExpenseForm().as_p()

    assert '<select name="user"' not in form

    assert '<input type="text" name="date"' in form

    assert '<select name="account"' in form
    assert '<select name="expense_type"' in form
    assert '<select name="expense_name"' in form

    assert '<input type="text" name="total_sum"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<input type="number" name="price"' in form
    assert '<textarea name="remark"' in form

    assert '<input type="checkbox" name="exception"' in form
    assert '<input type="file" name="attachment"' in form


@freeze_time('1000-01-01')
def test_expense_year_initial_value():
    UserFactory()

    form = ExpenseForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_expense_current_user_expense_types(second_user):
    ExpenseTypeFactory(title='T1')  # user bob, current user
    ExpenseTypeFactory(title='T2', journal=second_user.journal)  # user X

    form = ExpenseForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_expense_current_user_accounts(second_user):
    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = ExpenseForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_expense_select_first_account(second_user):
    AccountFactory(title='A1', journal=second_user.journal)
    a2 = AccountFactory(title='A2')

    form = ExpenseForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


def test_exepense_form_valid_data():
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t)

    form = ExpenseForm(
        data={
            'date': '1999-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': None
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1999, 1, 1)
    assert e.price == round(Decimal(1.12), 2)
    assert e.expense_type == t
    assert e.expense_name == n
    assert e.account == a
    assert e.quantity == 1


@freeze_time('1999-1-1')
def test_exepense_insert_only_three_years_to_past():
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t)

    form = ExpenseForm(
        data={
            'date': '1995-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': None
        },
    )

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai negali būti mažesni nei 1996' in form.errors['date']


@freeze_time('1999-1-1')
def test_exepense_insert_only_one_year_to_futur():
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t)

    form = ExpenseForm(
        data={
            'date': '2001-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': None
        },
    )

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai negali būti didesni nei 2000' in form.errors['date']


def test_expenses_form_blank_data():
    form = ExpenseForm(data={})

    assert not form.is_valid()

    errors = {
        'date': ['Šis laukas yra privalomas.'],
        'price': ['Šis laukas yra privalomas.'],
        'quantity': ['Šis laukas yra privalomas.'],
        'expense_type': ['Šis laukas yra privalomas.'],
        'expense_name': ['Šis laukas yra privalomas.'],
        'account': ['Šis laukas yra privalomas.'],
    }
    assert form.errors == errors


@pytest.mark.parametrize(
    'file, ext, valid',
    [
        (small_gif, 'gif', True),
        (small_gif, 'jpeg', True),
        (small_gif, 'png', True),
        (b'x', 'pdf', False),
        (b'x', 'txt', False),
        (b'x', 'doc', False),
        (b'x', 'xls', False),
        (b'x', 'pdf', False),
    ]
)
def test_expenses_form_filefield(file, ext, valid):
    f = SimpleUploadedFile(f'x.{ext}', file, content_type=f'image/{ext}')
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t)

    form = ExpenseForm(
        data={
            'date': '1999-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': None,
        },
        files={'attachment': f}
    )

    assert form.is_valid() == valid


def test_exepense_form_attachment_too_big():
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t)

    def f():
        bts = BytesIO()
        sz = 1200
        img = Image.new("RGB", (sz, sz))
        img.save(bts, 'bmp')
        return SimpleUploadedFile("test.bmp", bts.getvalue(), content_type='image/bmp')

    form = ExpenseForm(
        data={
            'date': '1999-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': None
        },
        files={'attachment': f()}
    )

    assert not form.is_valid()
    assert 'attachment' in form.errors
    assert form.errors['attachment'] == ['Per didelis vaizdo failas ( > 4Mb)']


def test_exepense_form_necessary_type_and_exception():
    a = AccountFactory()
    t = ExpenseTypeFactory(necessary=True)
    n = ExpenseNameFactory(parent=t)

    form = ExpenseForm(
        data={
            'date': '1999-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': True
        },
    )

    assert not form.is_valid()

    assert form.errors == {
        'exception': ["Expense Type yra 'Būtina', todėl ji negali būti pažymėta kaip 'Išimtis'"]
    }


# ----------------------------------------------------------------------------
#                                                                 Expense Type
# ----------------------------------------------------------------------------
def test_expense_type_init():
    ExpenseTypeForm()


def test_expense_type_init_fields():
    form = ExpenseTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="checkbox" name="necessary"' in form
    assert '<select name="user"' not in form


def test_expense_type_valid_data():
    form = ExpenseTypeForm(data={
        'title': 'Title',
        'necessary': True
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.necessary
    assert data.journal.title == 'bob Journal'
    assert data.journal.users.first().username == 'bob'


def test_expense_type_blank_data():
    form = ExpenseTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'title' in form.errors


def test_expense_type_title_null():
    form = ExpenseTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_expense_type_title_too_long():
    form = ExpenseTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_expense_type_title_too_short():
    form = ExpenseTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_expense_type_unique_name():
    ExpenseTypeFactory(title='XXX')

    form = ExpenseTypeForm(
        data={
            'title': 'XXX',
        },
    )

    assert not form.is_valid()


# ----------------------------------------------------------------------------
#                                                                 Expense Name
# ----------------------------------------------------------------------------
def test_expense_name_init():
    ExpenseNameForm()


def test_expense_name_current_user_expense_types(second_user):
    ExpenseTypeFactory(title='T1') # user bob, current user
    ExpenseTypeFactory(title='T2', journal=second_user.journal) # user X

    form = ExpenseNameForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_expense_name_valid_data():
    p = ExpenseTypeFactory()

    form = ExpenseNameForm(data={
        'title': 'Title',
        'parent': p.pk,
        'valid_for': 1999
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.valid_for == 1999


def test_expense_name_blank_data():
    form = ExpenseNameForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors
    assert 'parent' in form.errors


def test_expense_name_title_null():
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': None, 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_expense_name_title_too_long():
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': 'a'*255, 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_expense_name_title_too_short():
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': 'x', 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors
