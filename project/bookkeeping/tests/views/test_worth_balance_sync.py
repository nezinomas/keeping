import pytest

from ... import balance_sources, views


@pytest.mark.parametrize(
    "view, sync",
    [
        (views.AccountsWorthNew, balance_sources.sync_accounts),
        (views.SavingsWorthNew, balance_sources.sync_savings),
        (views.PensionsWorthNew, balance_sources.sync_pensions),
    ],
)
def test_worth_view_syncs_its_own_balance(view, sync):
    assert view.balance_sync is sync
