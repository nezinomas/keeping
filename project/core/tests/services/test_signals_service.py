import pytest

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
from ...services import signals_service
from ...services.signals_service import journal_user, sync

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


def test_sync_hands_the_synchronizer_the_service_the_user_and_the_tables_df(
    main_user, mocker, monkeypatch
):
    get_data = mocker.Mock()
    synchronizer = mocker.Mock()
    table = mocker.Mock()
    monkeypatch.setattr(signals_service, "GetData", get_data)
    monkeypatch.setattr(signals_service, "BalanceSynchronizer", synchronizer)
    conf, service = {"incomes": ()}, mocker.Mock()

    sync(main_user, conf, table, service)

    get_data.assert_called_once_with(main_user, conf)
    table.assert_called_once_with(get_data.return_value)
    synchronizer.assert_called_once_with(service, main_user, table.return_value.df)
