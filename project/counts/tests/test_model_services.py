import re

import pytest
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock, patch

from ..services.model_services import CountModelService, CountTypeModelService


def test_count_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        CountModelService(user=None)


def test_count_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        CountModelService(user=anon)


@pytest.mark.django_db
def test_count_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    CountModelService(user=main_user)


def test_count_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        CountTypeModelService(user=None)


def test_count_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        CountTypeModelService(user=anon)


@pytest.mark.django_db
def test_count_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    CountTypeModelService(user=main_user)


@patch(
    "project.counts.services.model_services.CountTypeModelService.get_queryset",
    return_value="X",
)
def test_year_method_raises_not_implemented_error(mck):
    service = CountTypeModelService(user=MagicMock())

    expected_msg = "CountTypeModelService.year is not implemented. Use items() instead."
    with pytest.raises(NotImplementedError, match=re.escape(expected_msg)):
        service.year(2023)


@patch(
    "project.counts.services.model_services.CountTypeModelService.get_queryset",
    return_value="X",
)
def test_year_method_does_not_call_database(mck):
    service = CountTypeModelService(MagicMock())

    with pytest.raises(NotImplementedError):
        service.year(2023)

    mck.filter.assert_not_called()