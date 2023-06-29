import pytest
from django.urls import resolve, reverse

from .. import views
from ..factories import AccountFactory

pytestmark = pytest.mark.django_db


def test_view_lists_func():
    view = resolve("/accounts/")

    assert views.Lists is view.func.view_class


def test_view_new_func():
    view = resolve("/accounts/new/")

    assert views.New is view.func.view_class


def test_view_update_func():
    view = resolve("/accounts/update/1/")

    assert views.Update is view.func.view_class


def test_save_account(client_logged):
    data = {"title": "Title", "order": "111"}

    url = reverse("accounts:new")
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "Title" in actual


def test_accounts_save_invalid_data(client_logged):
    data = {"title": "", "order": "x"}

    url = reverse("accounts:new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert form.is_valid() is False


def test_account_update(client_logged):
    account = AccountFactory()
    data = {"title": "Title", "order": "111"}

    url = reverse("accounts:update", kwargs={"pk": account.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "Title" in actual


def test_account_not_load_other_journal(client_logged, second_user):
    AccountFactory(title="xxx")
    a2 = AccountFactory(title="yyy", journal=second_user.journal)

    url = reverse("accounts:update", kwargs={"pk": a2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_account_list_view_has_all(client_logged):
    AccountFactory(title="S1")
    AccountFactory(title="S2", closed=1974)

    url = reverse("accounts:list")
    response = client_logged.get(url)

    actual = response.context["object_list"]
    assert len(actual) == 2

    actual = actual.values_list("title", flat=True)
    assert "S1" in actual
    assert "S2" in actual


# ----------------------------------------------------------------------------
#                                                                 load_account
# ----------------------------------------------------------------------------
def test_load_to_account_func():
    view = resolve("/accounts/load/")

    assert views.LoadAccount is view.func.view_class


def test_load_to_account_form_200(tp, client_logged):
    assert tp.get_check_200("accounts:new")


def test_load_to_account_form_302(tp):
    response = tp.get("accounts:new")
    assert response.status_code == 302


def test_load_to_account_must_logged(tp):
    response = tp.get("accounts:load", follow=True)

    from ...users.views import Login

    assert response.resolver_match.func.view_class is Login


def test_load_to_account(tp, client_logged, second_user):
    a1 = AccountFactory(title="A1")
    AccountFactory(title="A2")
    AccountFactory(title="A3", journal=second_user.journal)

    tp.get("accounts:load", data={"from_account": a1.pk})

    assert len(tp.get_context("object_list")) == 1


def test_load_to_account_empty_parent(tp, client_logged):
    tp.get("accounts:load", data={"from_account": ""})

    assert tp.get_context("object_list") == []
