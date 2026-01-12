import re

import pytest
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock, patch

from ..services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
    SavingTypeModelService,
)


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


@patch(
    "project.savings.services.model_services.SavingTypeModelService.get_queryset",
    return_value="X",
)
def test_year_method_raises_not_implemented_error(mck):
    service = SavingTypeModelService(user=MagicMock())

    expected_msg = "SavingTypeModelService.year is not implemented. Use items() instead."
    with pytest.raises(NotImplementedError, match=re.escape(expected_msg)):
        service.year(2023)


@patch(
    "project.savings.services.model_services.SavingTypeModelService.get_queryset",
    return_value="X",
)
def test_year_method_does_not_call_database(mck):
    service = SavingTypeModelService(MagicMock())

    with pytest.raises(NotImplementedError):
        service.year(2023)

    mck.filter.assert_not_called()
