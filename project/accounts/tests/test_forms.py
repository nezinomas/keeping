from datetime import date

import pytest

from ..factories import AccountFactory
from ..forms import AccountForm


def test_account_init():
    AccountForm()


@pytest.mark.django_db
def test_account_valid_data():
    form = AccountForm(data={
        'title': 'Title',
        'order': '1'
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.order == 1


def test_account_blank_data():
    form = AccountForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors
    assert 'order' in form.errors
