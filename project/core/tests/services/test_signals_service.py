from copy import deepcopy

import pytest
from django.core.exceptions import ImproperlyConfigured

from ....bookkeeping.tests.factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from ....debts.tests.factories import BorrowFactory, BorrowReturnFactory
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import (
    SavingChangeFactory,
    SavingCloseFactory,
    TransactionFactory,
)
from ....users.tests.factories import UserFactory
from ...lib.signals import Accounts, Savings
from ...services import signals_service
from ...services.signals_service import (
    BalanceKind,
    journal_user,
    register_balance,
    register_sources,
    sync,
)

pytestmark = pytest.mark.django_db


def test_journal_user_is_the_first_user_of_the_journal(main_user):
    UserFactory(username="Y", email="y@y.yy", journal=main_user.journal)

    assert journal_user(SavingTypeFactory()) == main_user


@pytest.mark.parametrize(
    "factory",
    [
        IncomeFactory,
        ExpenseFactory,
        SavingFactory,
        TransactionFactory,
        SavingCloseFactory,
        SavingChangeFactory,
        BorrowFactory,
        BorrowReturnFactory,
        AccountWorthFactory,
        SavingWorthFactory,
        PensionWorthFactory,
        PensionFactory,
        SavingTypeFactory,
        PensionTypeFactory,
    ],
)
def test_journal_user_of_every_synced_model_is_the_journals_user(main_user, factory):
    assert journal_user(factory()) == main_user


# -------------------------------------------------------------------------------------
#                                                                     Balance registry
# -------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "kind, table, trigger",
    [
        (BalanceKind.ACCOUNTS, Accounts, "afterSignalAccounts"),
        (BalanceKind.SAVINGS, Savings, "afterSignalSavings"),
        (BalanceKind.PENSIONS, Savings, "afterSignalPensions"),
    ],
)
def test_balance_kind_knows_its_table_and_trigger(kind, table, trigger):
    assert kind.table is table
    assert kind.trigger == trigger


def test_balance_kind_values():
    assert [str(kind) for kind in BalanceKind] == ["accounts", "savings", "pensions"]


@pytest.mark.parametrize("kind", list(BalanceKind))
def test_sync_reads_the_source_registered_for_its_kind(
    kind, main_user, mocker, monkeypatch
):
    monkeypatch.setattr(signals_service, "_SOURCES", deepcopy(signals_service._SOURCES))
    monkeypatch.setattr(signals_service, "BalanceSynchronizer", mocker.Mock())
    source = mocker.Mock(return_value=[])
    register_sources("app", kind, "incomes", source)

    sync(kind, main_user)

    source.assert_called_once_with(main_user)


def test_source_of_another_kind_is_not_read(main_user, mocker, monkeypatch):
    monkeypatch.setattr(signals_service, "_SOURCES", deepcopy(signals_service._SOURCES))
    monkeypatch.setattr(signals_service, "BalanceSynchronizer", mocker.Mock())
    source = mocker.Mock(return_value=[])
    register_sources("app", BalanceKind.PENSIONS, "incomes", source)

    sync(BalanceKind.ACCOUNTS, main_user)

    source.assert_not_called()


def test_registering_an_apps_sources_again_replaces_them(
    main_user, mocker, monkeypatch
):
    monkeypatch.setattr(signals_service, "_SOURCES", deepcopy(signals_service._SOURCES))
    monkeypatch.setattr(signals_service, "BalanceSynchronizer", mocker.Mock())
    source = mocker.Mock(return_value=[])
    register_sources("app", BalanceKind.ACCOUNTS, "incomes", source)
    register_sources("app", BalanceKind.ACCOUNTS, "incomes", source)

    sync(BalanceKind.ACCOUNTS, main_user)

    source.assert_called_once_with(main_user)


def test_every_apps_sources_are_read(main_user, mocker, monkeypatch):
    monkeypatch.setattr(signals_service, "_SOURCES", deepcopy(signals_service._SOURCES))
    monkeypatch.setattr(signals_service, "BalanceSynchronizer", mocker.Mock())
    first, second = mocker.Mock(return_value=[]), mocker.Mock(return_value=[])
    register_sources("one", BalanceKind.ACCOUNTS, "incomes", first)
    register_sources("two", BalanceKind.ACCOUNTS, "incomes", second)

    sync(BalanceKind.ACCOUNTS, main_user)

    first.assert_called_once_with(main_user)
    second.assert_called_once_with(main_user)


@pytest.mark.parametrize("kind", list(BalanceKind))
def test_sync_hands_the_registered_balance_service_to_the_synchronizer(
    kind, main_user, mocker, monkeypatch
):
    synchronizer = mocker.Mock()
    monkeypatch.setattr(signals_service, "BalanceSynchronizer", synchronizer)
    monkeypatch.setattr(signals_service, "_BALANCES", {})
    service = mocker.Mock()
    register_balance(kind, service)

    sync(kind, main_user)

    assert synchronizer.call_args.args[:2] == (service, main_user)


@pytest.mark.parametrize("kind", list(BalanceKind))
def test_sync_without_a_balance_service_is_improperly_configured(
    kind, main_user, monkeypatch
):
    monkeypatch.setattr(signals_service, "_BALANCES", {})

    with pytest.raises(ImproperlyConfigured):
        sync(kind, main_user)


@pytest.mark.parametrize("part", ["income", "Incomes", ""])
def test_source_under_an_unknown_part_is_refused(part, mocker, monkeypatch):
    monkeypatch.setattr(signals_service, "_SOURCES", deepcopy(signals_service._SOURCES))

    with pytest.raises(ValueError, match=f"'{part}'"):
        register_sources("app", BalanceKind.ACCOUNTS, part, mocker.Mock())

    assert part not in signals_service._SOURCES[BalanceKind.ACCOUNTS]


@pytest.mark.parametrize("kind", list(BalanceKind))
def test_sync_calls_the_kinds_entry_point(kind, main_user, mocker):
    entry = mocker.patch(f"project.core.services.signals_service.sync_{kind}")

    sync(kind, main_user)

    entry.assert_called_once_with(main_user)
