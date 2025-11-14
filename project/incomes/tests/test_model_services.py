import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import IncomeModelService, IncomeTypeModelService


def test_income_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        IncomeModelService(user=None)


def test_income_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        IncomeModelService(user=anon)


@pytest.mark.django_db
def test_income_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    IncomeModelService(user=main_user)


def test_income_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        IncomeTypeModelService(user=None)


def test_income_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        IncomeTypeModelService(user=anon)


@pytest.mark.django_db
def test_income_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    IncomeTypeModelService(user=main_user)
