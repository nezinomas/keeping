import pytest

from ..forms import AccountForm


def test_account_init():
    AccountForm()


def test_account_form_has_fields():
    form = AccountForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="number" name="order"' in form
    assert '<select name="user"' not in form


@pytest.mark.django_db
def test_account_valid_data(get_user):
    form = AccountForm(data={
        'title': 'Title',
        'order': '1'
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.order == 1
    assert data.user.username == 'bob'


def test_account_blank_data():
    form = AccountForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors
    assert 'order' in form.errors
