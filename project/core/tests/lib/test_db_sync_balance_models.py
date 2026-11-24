import pytest

from ....accounts.models import AccountBalance
from ....core.lib.db_sync import ACCOUNT_FIELDS, SAVING_FIELDS
from ....pensions.models import PensionBalance
from ....savings.models import SavingBalance


@pytest.mark.parametrize(
    "model, owner_field, sync_fields",
    [
        (AccountBalance, "account", ACCOUNT_FIELDS),
        (SavingBalance, "saving_type", SAVING_FIELDS),
        (PensionBalance, "pension_type", SAVING_FIELDS),
    ],
)
def test_balance_model_names_its_owner_and_sync_fields(model, owner_field, sync_fields):
    assert model.owner_field == owner_field
    assert model.sync_fields == sync_fields
    assert model._meta.get_field(owner_field).column == f"{owner_field}_id"
