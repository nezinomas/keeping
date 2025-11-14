import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import SavingModelService, SavingTypeModelService, SavingBalanceModelService


def test_saving_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingModelService(user=None)


def test_saving_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingModelService(user=anon)


@pytest.mark.django_db
def test_saving_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingModelService(user=main_user)


def test_saving_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingTypeModelService(user=None)


def test_saving_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingTypeModelService(user=anon)


@pytest.mark.django_db
def test_saving_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingTypeModelService(user=main_user)


def test_saving_balance_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingBalanceModelService(user=None)


def test_saving_balance_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingBalanceModelService(user=anon)


@pytest.mark.django_db
def test_saving_balance_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingBalanceModelService(user=main_user)
