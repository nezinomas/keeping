import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import (
    PensionBalanceModelService,
    PensionModelService,
    PensionTypeModelService,
)


def test_pension_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        PensionModelService(user=None)


def test_pension_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        PensionModelService(user=anon)


@pytest.mark.django_db
def test_pension_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    PensionModelService(user=main_user)


def test_pension_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        PensionTypeModelService(user=None)


def test_pension_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        PensionTypeModelService(user=anon)


@pytest.mark.django_db
def test_pension_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    PensionTypeModelService(user=main_user)


def test_pension_balance_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        PensionBalanceModelService(user=None)


def test_pension_balance_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        PensionBalanceModelService(user=anon)


@pytest.mark.django_db
def test_pension_balance_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    PensionBalanceModelService(user=main_user)
