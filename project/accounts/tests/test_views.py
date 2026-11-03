import json
import re

import pytest
from django.urls import reverse

from ...users.views import Login
from .factories import AccountFactory

pytestmark = pytest.mark.django_db


SAVED_ROW = (
    r'<tr hx-get="[^"]*" hx-trigger="dblclick"[^>]*>\s*<td class="text-left">Title</td>'
)


def test_save_account(client_logged):
    data = {"title": "Title", "order": "111"}

    url = reverse("accounts:new")
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert response.redirect_chain == [("/transactions/accounts/open/", 302)]
    assert re.search(SAVED_ROW, actual)


def test_accounts_save_invalid_data(client_logged):
    data = {"title": "", "order": "x"}

    url = reverse("accounts:new")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert actual.count('aria-invalid="true"') == 2


def test_account_update(client_logged):
    account = AccountFactory()
    data = {"title": "Title", "order": "111"}

    url = reverse("accounts:update", kwargs={"pk": account.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert response.redirect_chain == [("/transactions/accounts/open/", 302)]
    assert re.search(SAVED_ROW, actual)


@pytest.mark.parametrize(
    "url_of",
    [
        pytest.param(lambda account: reverse("accounts:new"), id="new"),
        pytest.param(
            lambda account: reverse("accounts:update", kwargs={"pk": account.pk}),
            id="update",
        ),
    ],
)
def test_an_account_form_fires_reload(client_logged, url_of):
    account = AccountFactory()
    data = {"title": "Title", "order": "111"}

    response = client_logged.post(url_of(account), data, headers={"HX-Request": "true"})

    assert json.loads(response.headers["HX-Trigger"]) == {"reload": {}}


def test_account_not_load_other_journal(client_logged, second_user):
    AccountFactory(title="xxx")
    a2 = AccountFactory(title="yyy", journal=second_user.journal)

    url = reverse("accounts:update", kwargs={"pk": a2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_an_account_closed_before_the_year_opens_its_form(client_logged, main_user):
    main_user.year = 2022
    main_user.save()
    account = AccountFactory(title="Old", closed=2021)

    url = reverse("accounts:update", kwargs={"pk": account.pk})
    actual = client_logged.get(url).content.decode("utf-8")

    assert re.search(r'<input type="text" name="title" value="Old"', actual)


def test_accounts_have_no_page_of_their_own(client_logged):
    AccountFactory(title="S1")

    assert client_logged.get("/accounts/").status_code == 404


def test_new_form_renders_the_title_field(client_logged):
    url = reverse("accounts:new")
    response = client_logged.get(url)

    assert response.status_code == 200
    assert 'name="title"' in response.content.decode("utf-8")


def test_new_form_redirects_anonymous_to_login(tp):
    response = tp.get("accounts:new")

    assert response.status_code == 302
    assert response.url.startswith(reverse("users:login"))


def test_load_to_account_must_logged(tp):
    response = tp.get("accounts:load", follow=True)

    assert response.resolver_match.func.view_class is Login


def test_load_to_account(tp, client_logged, second_user):
    a1 = AccountFactory(title="A1")
    AccountFactory(title="A2")
    AccountFactory(title="A3", journal=second_user.journal)

    tp.get("accounts:load", data={"from_account": a1.pk})

    assert [account.title for account in tp.get_context("object_list")] == ["A2"]


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-value"),
        pytest.param({"from_account": ""}, id="empty"),
        pytest.param({"from_account": "x"}, id="not-a-number"),
        pytest.param({"from_account": "0"}, id="zero"),
    ],
)
def test_load_to_account_empty_parent(tp, client_logged, data):
    AccountFactory(title="A1")

    tp.get("accounts:load", data=data)

    assert tp.get_context("object_list") == []
