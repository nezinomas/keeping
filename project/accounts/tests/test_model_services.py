import re

import pytest
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock

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


def test_year_method_raises_not_implemented_error(mocker):
    mocker.patch(
        "project.accounts.services.model_services.AccountModelService.get_queryset",
        return_value="X",
    )
    service = AccountModelService(user=MagicMock())

    expected_msg = "AccountModelService.year is not implemented. Use items() instead."
    with pytest.raises(NotImplementedError, match=re.escape(expected_msg)):
        service.year(2023)


def test_year_method_does_not_call_database_pure_pytest(mocker):
    mock_qs = mocker.MagicMock()
    mocker.patch(
        "project.accounts.services.model_services.AccountModelService.get_queryset",
        return_value=mock_qs
    )

    service = AccountModelService(mocker.MagicMock())
    with pytest.raises(NotImplementedError):
        service.year(2023)

    mock_qs.filter.assert_not_called()
