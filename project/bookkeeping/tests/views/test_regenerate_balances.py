import json
from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....accounts.tests.factories import AccountBalance
from ....core.tests.utils import setup_view
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....journals.tests.factories import JournalFactory
from ....pensions.tests.factories import PensionBalance, PensionFactory
from ....savings.tests.factories import SavingBalance, SavingFactory
from ....users.tests.factories import UserFactory
from ... import views

pytestmark = pytest.mark.django_db


def test_view_regenerate_balances_responds_no_content(client_logged):
    url = reverse("bookkeeping:regenerate_balances")
    response = client_logged.get(url, follow=True)

    assert response.status_code == 204


@time_machine.travel("1999-01-01")
def test_view_regenerate_balances_all_year(client_logged, main_user):
    ExpenseFactory()
    ExpenseFactory(date=date(1998, 1, 1))

    IncomeFactory()
    IncomeFactory(date=date(1998, 1, 1))

    SavingFactory()
    PensionFactory()

    main_user.journal.first_record = date(1998, 1, 1)
    main_user.journal.save()

    AccountBalance.objects.all().delete()
    SavingBalance.objects.all().delete()
    PensionBalance.objects.all().delete()

    assert AccountBalance.objects.all().count() == 0
    assert SavingBalance.objects.all().count() == 0
    assert PensionBalance.objects.all().count() == 0

    url = reverse("bookkeeping:regenerate_balances")

    client_logged.get(url, follow=True)

    assert AccountBalance.objects.all().count() == 3
    assert SavingBalance.objects.all().count() == 2
    assert PensionBalance.objects.all().count() == 2


def test_view_regenerate_syncs_every_balance_and_reloads_the_tab(mocker, rf):
    request = rf.get("/fake/")
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()
    syncs = [
        mocker.patch(f"project.bookkeeping.balance_sources.sync_{name}")
        for name in ("accounts", "savings", "pensions")
    ]

    response = setup_view(views.RegenerateBalances(), request).get(request)

    assert tuple(sync.call_count for sync in syncs) == (1, 1, 1)
    assert json.loads(response.headers["HX-Trigger"]) == {"reload": {}}
