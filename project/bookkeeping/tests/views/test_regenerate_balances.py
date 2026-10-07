import json
from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse

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


def test_view_regenerate_balances_func():
    view = resolve("/set/balances/")

    assert views.RegenerateBalances == view.func.view_class


def test_view_regenerate_balances_status_200(client_logged):
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

    client_logged.get(url, {"ajax_trigger": 1}, follow=True)

    assert AccountBalance.objects.all().count() == 3
    assert SavingBalance.objects.all().count() == 2
    assert PensionBalance.objects.all().count() == 2


def test_view_regenerate_balances_func_called(mocker, fake_request):
    account = mocker.patch("project.bookkeeping.balance_sources.sync_accounts")
    saving = mocker.patch("project.bookkeeping.balance_sources.sync_savings")
    pension = mocker.patch("project.bookkeeping.balance_sources.sync_pensions")

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), fake_request)
    view.get(fake_request)

    assert account.call_count == 1
    assert saving.call_count == 1
    assert pension.call_count == 1


def test_view_regenerate_account_balances(mocker, rf):
    request = rf.get("/fake/?type=accounts")

    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()

    account = mocker.patch("project.bookkeeping.balance_sources.sync_accounts")
    saving = mocker.patch("project.bookkeeping.balance_sources.sync_savings")
    pension = mocker.patch("project.bookkeeping.balance_sources.sync_pensions")

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 1
    assert saving.call_count == 0
    assert pension.call_count == 0


def test_view_regenerate_saving_balances(mocker, rf):
    request = rf.get("/fake/?type=savings")
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()

    account = mocker.patch("project.bookkeeping.balance_sources.sync_accounts")
    saving = mocker.patch("project.bookkeeping.balance_sources.sync_savings")
    pension = mocker.patch("project.bookkeeping.balance_sources.sync_pensions")

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 0
    assert saving.call_count == 1
    assert pension.call_count == 0


def test_view_regenerate_pension_balances(mocker, rf):
    request = rf.get("/fake/?type=pensions")
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()

    account = mocker.patch("project.bookkeeping.balance_sources.sync_accounts")
    saving = mocker.patch("project.bookkeeping.balance_sources.sync_savings")
    pension = mocker.patch("project.bookkeeping.balance_sources.sync_pensions")

    class Dummy(views.RegenerateBalances):
        pass

    view = setup_view(Dummy(), request)
    view.get(request)

    assert account.call_count == 0
    assert saving.call_count == 0
    assert pension.call_count == 1


@pytest.mark.parametrize(
    "kind, trigger",
    [
        ("accounts", "afterSignalAccounts"),
        ("savings", "afterSignalSavings"),
        ("pensions", "afterSignalPensions"),
    ],
)
def test_view_regenerate_sends_the_trigger_of_its_kind(kind, trigger, mocker, rf):
    request = rf.get(f"/fake/?type={kind}")
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()
    mocker.patch("project.bookkeeping.balance_sources.sync_accounts")
    mocker.patch("project.bookkeeping.balance_sources.sync_savings")
    mocker.patch("project.bookkeeping.balance_sources.sync_pensions")

    response = setup_view(views.RegenerateBalances(), request).get(request)

    assert json.loads(response.headers["HX-Trigger"]) == {trigger: {}}


def test_view_regenerate_unknown_type_syncs_all_and_sends_after_signal(mocker, rf):
    request = rf.get("/fake/?type=xxx")
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()
    syncs = [
        mocker.patch(f"project.bookkeeping.balance_sources.sync_{kind}")
        for kind in ("accounts", "savings", "pensions")
    ]

    response = setup_view(views.RegenerateBalances(), request).get(request)

    assert [x.call_count for x in syncs] == [1, 1, 1]
    assert json.loads(response.headers["HX-Trigger"]) == {"afterSignal": {}}


def test_view_regenerate_no_errors(client_logged):
    url = reverse("bookkeeping:regenerate_balances")
    response = client_logged.get(f"{url}?type=xxx&ajax_trigger=1", {})

    assert response.status_code == 204
