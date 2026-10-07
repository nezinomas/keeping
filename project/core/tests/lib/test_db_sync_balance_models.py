import pytest

from ....accounts.models import AccountBalance
from ....core.lib.db_sync import ACCOUNT_FIELDS, SAVING_FIELDS
from ....pensions.models import PensionBalance
from ....savings.models import SavingBalance


@pytest.mark.parametrize(
    "model, fund_field, sync_fields",
    [
        (AccountBalance, "account", ACCOUNT_FIELDS),
        (SavingBalance, "saving_type", SAVING_FIELDS),
        (PensionBalance, "pension_type", SAVING_FIELDS),
    ],
)
def test_balance_model_names_its_fund_and_sync_fields(model, fund_field, sync_fields):
    assert model.fund_field == fund_field
    assert model.sync_fields == sync_fields
    assert model._meta.get_field(fund_field).column == f"{fund_field}_id"
