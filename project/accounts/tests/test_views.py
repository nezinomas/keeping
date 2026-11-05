import json
import re

import pytest
from django.urls import reverse

from .factories import AccountFactory

pytestmark = pytest.mark.django_db


SAVED_ROW = (
    r'<tr hx-get="[^"]*" hx-trigger="dblclick"[^>]*>\s*'
    r'<td class="text-left main__name">Title</td>'
)


BY_FORM = pytest.mark.parametrize(
    "url_of",
    [
        pytest.param(lambda account: reverse("accounts:new"), id="new"),
        pytest.param(
            lambda account: reverse("accounts:update", kwargs={"pk": account.pk}),
            id="update",
        ),
    ],
)


@BY_FORM
def test_an_account_save_lands_on_its_tab(client_logged, url_of):
    account = AccountFactory()
    data = {"title": "Title", "order": "111"}

    response = client_logged.post(url_of(account), data, follow=True)
    actual = response.content.decode("utf-8")

    assert response.redirect_chain == [("/transactions/accounts/", 302)]
    assert re.search(SAVED_ROW, actual)


def test_accounts_save_invalid_data(client_logged):
    data = {"title": "", "order": "x"}

    url = reverse("accounts:new")
    response = client_logged.post(url, data)
    actual = response.content.decode("utf-8")

    assert re.findall(r'name="(\w+)"[^>]*aria-invalid="true"', actual) == [
        "title",
        "order",
    ]


@BY_FORM
def test_an_account_form_fires_reload(client_logged, url_of):
    account = AccountFactory()
    data = {"title": "Title", "order": "111"}

    response = client_logged.post(url_of(account), data, headers={"HX-Request": "true"})

    assert json.loads(response.headers.get("HX-Trigger", "null")) == {"reload": {}}


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
    assert client_logged.get("/accounts/").status_code == 404


def test_new_form_renders_the_title_field(client_logged):
    url = reverse("accounts:new")
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert '<h5 class="modal-title">Sąskaita</h5>' in actual
    assert 'name="title"' in actual
