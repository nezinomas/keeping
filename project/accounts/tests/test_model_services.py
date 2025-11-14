import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import AccountBalanceModelService, AccountModelService


def test_balance_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        AccountBalanceModelService(user=None)


def test_balance_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        AccountBalanceModelService(user=anon)


@pytest.mark.django_db
def test_balance_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    AccountBalanceModelService(user=main_user)


def test_account_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        AccountModelService(user=None)


def test_account_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        AccountModelService(user=anon)


@pytest.mark.django_db
def test_account_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    AccountModelService(user=main_user)
