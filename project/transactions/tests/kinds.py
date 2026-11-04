from collections.abc import Callable
from typing import NamedTuple

import pytest

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...savings.models import SavingBalance
from ...savings.tests.factories import SavingTypeFactory
from .. import models
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm
from ..services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)
from .factories import SavingChangeFactory, SavingCloseFactory, TransactionFactory


class Kind(NamedTuple):
    """One kind of Move, and what a test builds, posts or reads it through."""

    model: type
    factory: type
    from_factory: type
    to_factory: type
    form: type
    service: type
    received: Callable
    fund_move: bool
    new_url: str
    update_url: str
    delete_url: str
    tab_url: str
    modal_title: str
    from_title: str
    to_title: str
    delete_text: str


def _account_1999(account):
    return AccountBalance.objects.get(account=account, year=1999)


def _fund_1999(fund):
    return SavingBalance.objects.get(saving_type=fund, year=1999)


KINDS = {
    "transaction": Kind(
        model=models.Transaction,
        factory=TransactionFactory,
        from_factory=AccountFactory,
        to_factory=AccountFactory,
        form=TransactionForm,
        service=TransactionModelService,
        received=_account_1999,
        fund_move=False,
        new_url="transactions:new",
        update_url="transactions:update",
        delete_url="transactions:delete",
        tab_url="transactions:index",
        modal_title="Pinigų pervedimas",
        from_title="Account1",
        to_title="Account2",
        delete_text="1999-01-01 Account1 -&gt; Account2: 2,00",
    ),
    "sale": Kind(
        model=models.SavingClose,
        factory=SavingCloseFactory,
        from_factory=SavingTypeFactory,
        to_factory=AccountFactory,
        form=SavingCloseForm,
        service=SavingCloseModelService,
        received=_account_1999,
        fund_move=True,
        new_url="transactions:savings_close_new",
        update_url="transactions:savings_close_update",
        delete_url="transactions:savings_close_delete",
        tab_url="transactions:tab_sales",
        modal_title="Fondas ⇒ Sąskaita",
        from_title="Savings From",
        to_title="Account To",
        delete_text="1999-01-01 Savings From -&gt; Account To: 0,10",
    ),
    "switch": Kind(
        model=models.SavingChange,
        factory=SavingChangeFactory,
        from_factory=SavingTypeFactory,
        to_factory=SavingTypeFactory,
        form=SavingChangeForm,
        service=SavingChangeModelService,
        received=_fund_1999,
        fund_move=True,
        new_url="transactions:savings_change_new",
        update_url="transactions:savings_change_update",
        delete_url="transactions:savings_change_delete",
        tab_url="transactions:tab_switches",
        modal_title="Fondas ⇔ Fondas",
        from_title="Savings From",
        to_title="Savings To",
        delete_text="1999-01-01 Savings From -&gt; Savings To: 0,10",
    ),
}
FUND_MOVES = {name: kind for name, kind in KINDS.items() if kind.fund_move}

by_kind = pytest.mark.parametrize("kind", KINDS.values(), ids=KINDS.keys())
by_fund_move = pytest.mark.parametrize(
    "kind", FUND_MOVES.values(), ids=FUND_MOVES.keys()
)
