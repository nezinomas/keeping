import pytest
from django.contrib.auth.models import AnonymousUser

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
