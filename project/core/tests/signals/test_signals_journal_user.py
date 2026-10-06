import pytest

from ....pensions.tests.factories import PensionTypeFactory
from ....savings.tests.factories import SavingTypeFactory
from ...services import signals_service

pytestmark = pytest.mark.django_db


def test_saving_type_save_syncs_accounts_once_and_savings_once(main_user, mocker):
    fund = SavingTypeFactory(title="Fund")
    accounts = mocker.spy(signals_service, "sync_accounts")
    savings = mocker.spy(signals_service, "sync_savings")

    fund.save()

    assert accounts.call_args_list == [mocker.call(main_user)]
    assert savings.call_args_list == [mocker.call(main_user)]


def test_pension_type_save_syncs_pensions_once(main_user, mocker):
    pension_type = PensionTypeFactory(title="Pension")
    pensions = mocker.spy(signals_service, "sync_pensions")

    pension_type.save()

    assert pensions.call_args_list == [mocker.call(main_user)]
