import pytest

from ....bookkeeping import balance_sources
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.tests.factories import SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db


def test_saving_type_save_syncs_accounts_once_and_savings_once(main_user, mocker):
    fund = SavingTypeFactory(title="Fund")
    accounts = mocker.spy(balance_sources, "sync_accounts")
    savings = mocker.spy(balance_sources, "sync_savings")

    fund.save()

    assert accounts.call_args_list == [mocker.call(main_user)]
    assert savings.call_args_list == [mocker.call(main_user)]


def test_pension_type_save_syncs_pensions_once(main_user, mocker):
    pension_type = PensionTypeFactory(title="Pension")
    pensions = mocker.spy(balance_sources, "sync_pensions")

    pension_type.save()

    assert pensions.call_args_list == [mocker.call(main_user)]


@pytest.mark.parametrize(
    "factory, sync",
    [
        pytest.param(IncomeFactory, "sync_accounts", id="income"),
        pytest.param(SavingFactory, "sync_savings", id="saving"),
        pytest.param(PensionFactory, "sync_pensions", id="pension"),
    ],
)
def test_save_syncs_with_the_journals_user(main_user, mocker, factory, sync):
    spy = mocker.spy(balance_sources, sync)

    factory()

    assert mocker.call(main_user) in spy.call_args_list
