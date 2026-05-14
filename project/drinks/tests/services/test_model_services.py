import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import DrinkModelService, DrinkTargetModelService


def test_drink_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        DrinkModelService(user=None)


def test_drink_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        DrinkModelService(user=anon)


@pytest.mark.django_db
def test_drink_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    DrinkModelService(user=main_user)


def test_drink_target_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        DrinkTargetModelService(user=None)


def test_drink_target_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        DrinkTargetModelService(user=anon)


@pytest.mark.django_db
def test_drink_target_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    DrinkTargetModelService(user=main_user)
