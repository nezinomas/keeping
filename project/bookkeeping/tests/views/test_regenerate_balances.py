import json
import re
from datetime import date

import pytest
import time_machine
from django.test import Client
from django.urls import reverse

from ....accounts.tests.factories import AccountBalance
from ....core.tests.utils import setup_view, tab_fragment
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....journals.tests.factories import JournalFactory
from ....pensions.tests.factories import PensionBalance, PensionFactory
from ....savings.tests.factories import SavingBalance, SavingFactory
from ....users.tests.factories import UserFactory
from ... import views

pytestmark = pytest.mark.django_db


BALANCES = (AccountBalance, SavingBalance, PensionBalance)


def test_a_get_is_refused_and_syncs_nothing(client_logged):
    IncomeFactory()
    SavingFactory()
    PensionFactory()
    for balance in BALANCES:
        balance.objects.all().delete()

    response = client_logged.get(reverse("bookkeeping:regenerate_balances"))

    assert [response.status_code, *(b.objects.count() for b in BALANCES)] == [
        405,
        0,
        0,
        0,
    ]


def test_a_post_passes_csrf_only_with_each_icons_token(main_user):
    IncomeFactory()
    SavingFactory()
    PensionFactory()
    client = Client(enforce_csrf_checks=True)
    client.force_login(main_user)
    content = "".join(
        tab_fragment(client, reverse(url_name))
        for url_name in ("bookkeeping:tab_overview", "bookkeeping:tab_funds")
    )
    tokens = re.findall(
        r'<button\b[^>]*\bid="refresh-(\w+)"[^>]*'
        r'\bhx-headers=\'\{"X-CSRFToken":"([^"]+)"\}\'',
        content,
    )
    url = reverse("bookkeeping:regenerate_balances")

    statuses = [
        ("no token", client.post(url).status_code),
        *(
            (kind, client.post(url, headers={"X-CSRFToken": token}).status_code)
            for kind, token in tokens
        ),
    ]

    assert statuses == [
        ("no token", 403),
        ("accounts", 204),
        ("savings", 204),
        ("pensions", 204),
    ]


def test_an_anonymous_post_lands_on_the_login(client):
    url = reverse("bookkeeping:regenerate_balances")

    response = client.post(url)

    assert response.url == f"{reverse('users:login')}?next={url}"


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

    response = client_logged.post(url, follow=True)

    assert response.status_code == 204
    assert AccountBalance.objects.all().count() == 3
    assert SavingBalance.objects.all().count() == 2
    assert PensionBalance.objects.all().count() == 2


def test_view_regenerate_syncs_every_balance_and_reloads_the_tab(mocker, rf):
    request = rf.post("/fake/")
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()
    syncs = [
        mocker.patch(f"project.bookkeeping.balance_sources.sync_{name}")
        for name in ("accounts", "savings", "pensions")
    ]

    response = setup_view(views.RegenerateBalances(), request).post(request)

    assert tuple(sync.call_count for sync in syncs) == (1, 1, 1)
    assert json.loads(response.headers["HX-Trigger"]) == {"reload": {}}
