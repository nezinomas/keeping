from decimal import Decimal

import pytest
from django.urls import resolve, reverse

from ...accounts.factories import AccountFactory
from .. import models, views
from ..factories import AccountWorthFactory

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                     Account Worth Reset
# ---------------------------------------------------------------------------------------
def test_account_worth_reset_func():
    view = resolve('/bookkeeping/accounts_worth/reset/1/')

    assert views.AccountsWorthReset == view.func.view_class


def test_account_worth_reset_200(client_logged):
    a = AccountWorthFactory()
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_account_worth_reset_302(client):
    a = AccountWorthFactory()
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.pk})
    response = client.get(url)

    assert response.status_code == 302


def test_account_worth_reset_404(client_logged):
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': 1})
    response = client_logged.get(url)

    assert response.status_code == 204


def test_account_worth_reset_string_404(client_logged):
    url = '/bookkeeping/accounts_worth/reset/x/'
    response = client_logged.get(url)

    assert response.status_code == 404


def test_account_worth_reset_already_reseted(client_logged):
    a = AccountWorthFactory(price=0)

    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.account.pk})
    response = client_logged.get(url)

    assert response.status_code == 204


def test_account_worth_reset(client_logged):
    a = AccountWorthFactory()

    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.account.pk})
    client_logged.get(url)

    actual = models.AccountWorth.objects.latest('id')

    assert actual.price == Decimal(0.0)

    actual = models.AccountWorth.objects.all()

    assert actual.count() == 2


def test_account_worth_reset_no_object(client_logged):
    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': 1})
    client_logged.get(url)

    actual = models.AccountWorth.objects.all()

    assert actual.count() == 0


def test_account_worth_reset_other_journal_account(client_logged, main_user, second_user):
    j1 = main_user.journal
    j2 = second_user.journal
    a1 = AccountFactory(title='x', journal=j1)
    a2 = AccountFactory(title='y', journal=j2)
    AccountWorthFactory(account=a1, price=777)
    AccountWorthFactory(account=a2, price=666)

    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a2.pk})
    response = client_logged.get(url)

    assert response.status_code == 204
    assert models.AccountWorth.objects.latest('id').price == Decimal('666')


def test_account_worth_reset_no_worth_record(client_logged):
    a = AccountFactory()

    url = reverse('bookkeeping:accounts_worth_reset', kwargs={'pk': a.pk})
    response = client_logged.get(url)

    assert response.status_code == 204
