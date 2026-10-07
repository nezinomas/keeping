import pytest

from ...core.services.signals_service import BalanceKind
from ..models import AccountWorth, PensionWorth, SavingWorth


@pytest.mark.parametrize(
    "model, name",
    [
        (AccountWorth, "account"),
        (SavingWorth, "saving_type"),
        (PensionWorth, "pension_type"),
    ],
)
def test_worth_model_names_its_fund_field(model, name):
    assert model.fund_field == name
    assert model._meta.get_field(name).many_to_one


@pytest.mark.parametrize(
    "model, kind",
    [
        (AccountWorth, BalanceKind.ACCOUNTS),
        (SavingWorth, BalanceKind.SAVINGS),
        (PensionWorth, BalanceKind.PENSIONS),
    ],
)
def test_worth_model_names_its_balance_kind(model, kind):
    assert model.balance_kind == kind
