import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import DebtModelService, DebtReturnModelService


def test_debt_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        DebtModelService(user=None, debt_type="X")


def test_debt_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        DebtModelService(user=anon, debt_type="X")


@pytest.mark.django_db
def test_debt_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    DebtModelService(user=main_user, debt_type="X")


def test_debt_return_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        DebtReturnModelService(user=None, debt_type="X")


def test_debt_return_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        DebtReturnModelService(user=anon, debt_type="X")


@pytest.mark.django_db
def test_debt_return_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    DebtReturnModelService(user=main_user, debt_type="X")
