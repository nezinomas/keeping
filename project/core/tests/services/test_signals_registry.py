import pytest

from ....accounts.services.model_services import AccountBalanceModelService
from ....pensions.services.model_services import PensionBalanceModelService
from ....savings.services.model_services import SavingBalanceModelService
from ...services import signals_service
from ...services.signals_service import BalanceKind

ACCOUNTS, SAVINGS, PENSIONS = (
    BalanceKind.ACCOUNTS,
    BalanceKind.SAVINGS,
    BalanceKind.PENSIONS,
)

REGISTERED = {
    (ACCOUNTS, "incomes"): {"incomes": 1, "debts": 2, "transactions": 2},
    (ACCOUNTS, "expenses"): {
        "expenses": 1,
        "debts": 2,
        "transactions": 1,
        "savings": 1,
    },
    (ACCOUNTS, "have"): {"bookkeeping": 1},
    (ACCOUNTS, "types"): {"accounts": 1},
    (SAVINGS, "incomes"): {"savings": 1, "transactions": 1},
    (SAVINGS, "expenses"): {"transactions": 2},
    (SAVINGS, "moves"): {"transactions": 2},
    (SAVINGS, "have"): {"bookkeeping": 1},
    (SAVINGS, "types"): {"savings": 1},
    (PENSIONS, "incomes"): {"pensions": 1},
    (PENSIONS, "have"): {"bookkeeping": 1},
    (PENSIONS, "types"): {"pensions": 1},
}


@pytest.mark.parametrize("kind, part", list(REGISTERED))
def test_apps_contribute_these_sources(kind, part):
    registered = signals_service._SOURCES[kind][part]

    assert {app: len(sources) for app, sources in registered.items()} == REGISTERED[
        (kind, part)
    ]


def test_no_other_kind_or_part_is_registered():
    registered = {
        (kind, part)
        for kind, parts in signals_service._SOURCES.items()
        for part, apps in parts.items()
        if apps
    }

    assert registered == set(REGISTERED)


@pytest.mark.parametrize(
    "kind, service",
    [
        (ACCOUNTS, AccountBalanceModelService),
        (SAVINGS, SavingBalanceModelService),
        (PENSIONS, PensionBalanceModelService),
    ],
)
def test_each_kind_has_its_balance_service(kind, service):
    assert signals_service._BALANCES[kind] is service
