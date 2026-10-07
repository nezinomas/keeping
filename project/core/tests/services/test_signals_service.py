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
from ...services.signals_service import journal_user

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
