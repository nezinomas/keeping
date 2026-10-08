import re
from datetime import datetime

import pytest
import pytz
from django.urls import reverse

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountBalanceFactory, AccountFactory
from ....core.tests.utils import setup_view
from ... import views
from ...models import AccountWorth
from ..factories import AccountWorthFactory

pytestmark = pytest.mark.django_db


def test_formset(client_logged):
    AccountFactory()

    url = reverse("bookkeeping:accounts_worth_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Sąskaitų vertė" in actual
    assert '<option value="1" selected>Account1</option>' in actual


def test_formset_has_one_empty_price_per_account(client_logged):
    AccountFactory(title="A1")
    AccountFactory(title="A2")

    url = reverse("bookkeeping:accounts_worth_new")
    response = client_logged.get(url)

    prices = re.findall(
        r'<input[^>]*name="form-\d+-price"[^>]*>', response.content.decode()
    )
    assert len(prices) == 2
    assert not any("value=" in price for price in prices)


@pytest.mark.parametrize(
    "price, expected",
    [
        pytest.param("0.01", 1, id="new"),
        pytest.param("0", 0, id="null_value"),
    ],
)
def test_formset_new(client_logged, price, expected):
    i = AccountFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-9-9",
        "form-0-price": price,
        "form-0-account": i.pk,
    }

    url = reverse("bookkeeping:accounts_worth_new")
    client_logged.post(url, data, follow=True)

    actual = AccountWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 9
    assert actual.date.day == 9
    assert actual.price == expected


@pytest.mark.parametrize(
    "price, expected",
    [
        ("0.01", 1),
        ("4669.73", 466973),
        ("4669.736", 466973),
        ("466.73", 46673),  # Trap case: ensures binary noise is handled
    ],
)
def test_formset_new_post(client_logged, price, expected):
    i = AccountFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-9-9",
        "form-0-price": price,
        "form-0-account": i.pk,
    }

    url = reverse("bookkeeping:accounts_worth_new")
    client_logged.post(url, data, follow=True)

    actual = AccountBalance.objects.get(year=1999)
    assert actual.have == expected


def test_formset_new_post_save_empty_price(client_logged):
    a1 = AccountFactory()
    a2 = AccountFactory(title="X")
    data = {
        "form-TOTAL_FORMS": 2,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-9-9",
        "form-0-price": "0.01",
        "form-0-account": a1.pk,
        "form-1-date": "1999-9-9",
        "form-1-price": "",
        "form-1-account": a2.pk,
    }

    url = reverse("bookkeeping:accounts_worth_new")
    client_logged.post(url, data, follow=True)

    actual = AccountBalance.objects.get(year=1999)
    assert actual.have == 1


def test_formset_dublicated(client_logged):
    i = AccountFactory()
    data = {
        "form-TOTAL_FORMS": 2,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-9-9",
        "form-0-price": "999",
        "form-0-account": i.pk,
        "form-1-date": "1999-9-9",
        "form-1-price": "666",
        "form-1-account": i.pk,
    }

    url = reverse("bookkeeping:accounts_worth_new")
    response = client_logged.post(url, data)
    actual = response.context["formset"]

    assert not actual.is_valid()


def test_formset_invalid_data(client_logged):
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "x",
        "form-0-price": "x",
        "form-0-account": 0,
    }

    url = reverse("bookkeeping:accounts_worth_new")

    response = client_logged.post(url, data)
    actual = response.context["formset"]

    assert not actual.is_valid()
    assert "date" in actual.errors[0]
    assert "price" in actual.errors[0]
    assert "account" in actual.errors[0]


@pytest.mark.parametrize(
    "year, closed_listed",
    [
        pytest.param(2000, False, id="past"),
        pytest.param(1000, True, id="current"),
        pytest.param(1, True, id="future"),
    ],
)
def test_formset_lists_an_account_closed_in_the_users_year_or_later(
    main_user, rf, year, closed_listed
):
    AccountFactory(title="S1")
    AccountFactory(title="S2", closed=1000)

    main_user.year = year
    rf.user = main_user

    view = setup_view(views.AccountsWorthNew(), rf)

    actual = str(view.get_formset())

    assert "S1" in actual
    assert ("S2" in actual) is closed_listed


def test_view(client_logged):
    AccountWorthFactory(date=datetime(1111, 1, 1, tzinfo=pytz.utc), price=2)
    AccountWorthFactory(date=datetime(1999, 2, 2, tzinfo=pytz.utc), price=555)

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert 'data-tip="1999 m. vasario 2 d., 00:00"' in actual
    assert "5,55" in actual


def test_view_last_check_empty(client_logged):
    AccountBalanceFactory()

    url = reverse("bookkeeping:accounts")
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert 'data-tip="Nėra įrašo apie sąskaitos lėšas"' in actual
    assert '<td class="left-thick-border" data-cell="">0,20</td>' in actual
