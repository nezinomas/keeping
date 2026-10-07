from collections import defaultdict
from enum import StrEnum

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from ...users.models import User
from ..lib.db_sync import BalanceSynchronizer
from ..lib.signals import Accounts, GetData, Savings


class BalanceKind(StrEnum):
    ACCOUNTS = "accounts"
    SAVINGS = "savings"
    PENSIONS = "pensions"

    @property
    def table(self) -> type:
        return {
            BalanceKind.ACCOUNTS: Accounts,
            BalanceKind.SAVINGS: Savings,
            BalanceKind.PENSIONS: Savings,
        }[self]

    @property
    def trigger(self) -> str:
        return {
            BalanceKind.ACCOUNTS: "afterSignalAccounts",
            BalanceKind.SAVINGS: "afterSignalSavings",
            BalanceKind.PENSIONS: "afterSignalPensions",
        }[self]


_SOURCES: dict[BalanceKind, dict[str, dict[str, tuple]]] = defaultdict(
    lambda: defaultdict(dict)
)
_BALANCES: dict[BalanceKind, type] = {}


SOURCE_PARTS = frozenset({"incomes", "expenses", "moves", "have", "types"})


def register_sources(app_label: str, kind: BalanceKind, part: str, *sources) -> None:
    if part not in SOURCE_PARTS:
        raise ValueError(
            f"Unknown source part '{part}'; expected {sorted(SOURCE_PARTS)}."
        )
    _SOURCES[kind][part][app_label] = sources


def register_balance(kind: BalanceKind, service: type) -> None:
    _BALANCES[kind] = service


def sync(kind: BalanceKind, user: User):
    entry_points = {
        BalanceKind.ACCOUNTS: sync_accounts,
        BalanceKind.SAVINGS: sync_savings,
        BalanceKind.PENSIONS: sync_pensions,
    }
    entry_points[kind](user)


def sync_accounts(user: User):
    _sync_data(user, BalanceKind.ACCOUNTS)


def sync_savings(user: User):
    _sync_data(user, BalanceKind.SAVINGS)


def sync_pensions(user: User):
    _sync_data(user, BalanceKind.PENSIONS)


def _sync_data(user: User, kind: BalanceKind):
    if kind not in _BALANCES:
        raise ImproperlyConfigured(f"No balance service registered for {kind}.")

    data = kind.table(GetData(user, _flat_sources(kind)))
    BalanceSynchronizer(_BALANCES[kind], user, data.df)


def _flat_sources(kind: BalanceKind) -> dict[str, tuple]:
    return {
        part: tuple(source for sources in apps.values() for source in sources)
        for part, apps in _SOURCES[kind].items()
    }


def journal_user(instance: models.Model) -> User:
    return instance.journal.users.earliest("pk")
