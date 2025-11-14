import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)


def test_transaction_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        TransactionModelService(user=None)


def test_transaction_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        TransactionModelService(user=anon)


@pytest.mark.django_db
def test_transaction_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    TransactionModelService(user=main_user)


def test_saving_close_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingCloseModelService(user=None)


def test_saving_close_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingCloseModelService(user=anon)


@pytest.mark.django_db
def test_saving_close_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingCloseModelService(user=main_user)


def test_saving_change_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        SavingChangeModelService(user=None)


def test_saving_change_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        SavingChangeModelService(user=anon)


@pytest.mark.django_db
def test_saving_change_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    SavingChangeModelService(user=main_user)
