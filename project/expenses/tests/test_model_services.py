import pytest
from django.contrib.auth.models import AnonymousUser

from ..services.model_services import ExpenseModelService, ExpenseNameModelService, ExpenseTypeModelService


def test_expense_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseModelService(user=None)


def test_expense_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseModelService(user=anon)


@pytest.mark.django_db
def test_expense_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    ExpenseModelService(user=main_user)


def test_expense_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseTypeModelService(user=None)


def test_expense_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseTypeModelService(user=anon)


@pytest.mark.django_db
def test_expense_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    ExpenseTypeModelService(user=main_user)


def test_expense_name_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseNameModelService(user=None)


def test_expense_name_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseNameModelService(user=anon)


@pytest.mark.django_db
def test_expense_name_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    ExpenseNameModelService(user=main_user)
