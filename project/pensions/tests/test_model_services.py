import re

import pytest
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock, patch

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


@patch(
    "project.pensions.services.model_services.PensionTypeModelService.get_queryset",
    return_value="X",
)
def test_year_method_raises_not_implemented_error(mck):
    service = PensionTypeModelService(user=MagicMock())

    expected_msg = (
        "PensionTypeModelService.year is not implemented. Use items() instead."
    )
    with pytest.raises(NotImplementedError, match=re.escape(expected_msg)):
        service.year(2023)


@patch(
    "project.pensions.services.model_services.PensionTypeModelService.get_queryset",
    return_value="X",
)
def test_year_method_does_not_call_database(mck):
    service = PensionTypeModelService(MagicMock())

    with pytest.raises(NotImplementedError):
        service.year(2023)

    mck.filter.assert_not_called()
