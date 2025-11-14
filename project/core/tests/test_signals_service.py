import pytest
from mock import Mock

from ...incomes.factories import IncomeFactory
from ..services.signals_service import (
    _get_user_from_instance,
    sync_accounts,
    sync_pensions,
    sync_savings,
)


@pytest.mark.parametrize(
    "method_name",
    [
        (sync_accounts),
        (sync_savings),
        (sync_pensions),
    ],
)
def test_sync_accounts_returns_early_if_no_user(method_name):
    instance = Mock()
    instance._meta.get_fields.return_value = []

    result = method_name(instance)

    assert result is None  # returns early


@pytest.mark.parametrize(
    "method_name",
    [
        (sync_accounts),
        (sync_savings),
        (sync_pensions),
    ],
)
def test_sync_accounts_uses_provided_user(method_name, main_user):
    instance = Mock()

    with pytest.raises(AttributeError):
        method_name(instance, user=main_user)
    # No error = user was used, not _get_user_from_instance


def test__get_user_from_instance_returns_none_if_no_fk():
    instance = Mock()
    instance._meta.get_fields.return_value = []

    result = _get_user_from_instance(instance)

    assert result is None


def test__get_user_from_instance_returns_none_if_related_has_no_journal():
    instance = Mock()
    field = Mock()
    field.name = "account"
    field.many_to_one = True
    instance._meta.get_fields.return_value = [field]

    related = Mock()
    related.journal = None
    instance.account = related

    result = _get_user_from_instance(instance)

    assert result is None


def test__get_user_from_instance_returns_none_if_journal_has_no_users():
    instance = Mock()
    field = Mock(
        name="account",
        many_to_one=True,
    )
    instance._meta.get_fields.return_value = [field]

    journal = Mock()
    journal.users.first.return_value = None
    related = Mock(journal=journal)
    instance.account = related

    result = _get_user_from_instance(instance)

    assert result is None


@pytest.mark.django_db
def test__get_user_from_instance_returns_user_successfully(main_user):
    instance = IncomeFactory()
    result = _get_user_from_instance(instance)

    assert result == main_user
