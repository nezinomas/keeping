import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import BookModelService, BookTargetModelService


def test_book_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        BookModelService(user=None)


def test_book_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        BookModelService(user=anon)


@pytest.mark.django_db
def test_book_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    BookModelService(user=main_user)


def test_book_target_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        BookTargetModelService(user=None)


def test_book_target_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        BookTargetModelService(user=anon)


@pytest.mark.django_db
def test_book_target_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    BookTargetModelService(user=main_user)
