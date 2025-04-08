import pytest
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseTypeFactory
from ...journals.factories import JournalFactory
from ...journals.models import Journal
from ...users.factories import User, UserFactory
from .. import views

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                              Settings
# -------------------------------------------------------------------------------------
def test_settings_user_must_logged(client):
    url = reverse("users:settings_index")

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == "login"


def test_settings_link_if_user_is_superuser(client_logged):
    url = reverse("bookkeeping:index")

    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    link = reverse("users:settings_index")

    assert link in content


def test_settings_no_link_ordinary_user(main_user, client_logged):
    main_user.is_superuser = False
    main_user.save()

    url = reverse("bookkeeping:index")

    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    link = reverse("users:settings_index")

    assert link not in content


# -------------------------------------------------------------------------------------
#                                                                        Settings Index
# -------------------------------------------------------------------------------------
def test_index_func():
    view = resolve("/settings/")

    assert views.SettingsIndex == view.func.view_class


def test_index_user_must_be_superuser(main_user, client_logged):
    main_user.is_superuser = False
    main_user.save()

    url = reverse("users:settings_index")

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == "index"


def test_index_status_code(client_logged):
    url = reverse("users:settings_index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_context(client_logged):
    url = reverse("users:settings_index")
    response = client_logged.get(url)

    assert "users" in response.context
    assert "settings_unnecessary" in response.context
    assert "settings_journal" in response.context


# -------------------------------------------------------------------------------------
#                                                                        Settings Users
# -------------------------------------------------------------------------------------
def test_users_func():
    view = resolve("/settings/users/")

    assert views.SettingsUsers == view.func.view_class


def test_users_status_code(client_logged):
    url = reverse("users:settings_users")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_users_no_additional_users(client_logged):
    url = reverse("users:settings_users")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Nėra papildomų vartotojų." in actual


def test_users_one_additional_user(main_user, client_logged):
    UserFactory(
        username="X", email="x@x.x", is_superuser=False, journal=main_user.journal
    )
    UserFactory(username="Y", email="y@y.y", journal=JournalFactory(title="YY"))

    url = reverse("users:settings_users")
    response = client_logged.get(url)
    actual = response.context["object_list"]

    assert Journal.objects.all().count() == 2
    assert User.objects.all().count() == 3
    assert len(actual) == 1


def test_users_delete_func():
    view = resolve("/settings/users/delete/1/")

    assert views.SettingsUsersDelete is view.func.view_class


def test_users_delete_status_200(main_user, client_logged):
    u = UserFactory(username="X", email="x@x.x", journal=main_user.journal)

    url = reverse("users:settings_users_delete", kwargs={"pk": u.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_users_delete_load_form(main_user, client_logged):
    u1 = UserFactory(username="X", email="x@x.x", journal=main_user.journal)

    url = reverse("users:settings_users_delete", kwargs={"pk": u1.pk})
    response = client_logged.get(url, {})
    actual = response.content.decode()

    assert response.status_code == 200
    assert f"Ar tikrai norite ištrinti: <strong>{u1}</strong>?" in actual


def test_users_delete(main_user, client_logged):
    u1 = UserFactory(username="X", email="x@x.x", journal=main_user.journal)

    url = reverse("users:settings_users_delete", kwargs={"pk": u1.pk})
    client_logged.post(url, {})

    assert User.objects.all().count() == 1


def test_users_get_cant_delete_self(main_user, client_logged):
    url = reverse("users:settings_users_delete", kwargs={"pk": main_user.pk})
    response = client_logged.get(url, {})

    assert response.status_code == 404


def test_users_post_cant_delete_self(main_user, client_logged):
    url = reverse("users:settings_users_delete", kwargs={"pk": main_user.pk})
    response = client_logged.post(url)
    response.content.decode()

    assert User.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                  Unnecessary Expenses
# -------------------------------------------------------------------------------------
def test_unnecessary_func():
    view = resolve("/settings/unnecessary/")

    assert views.SettingsUnnecessary == view.func.view_class


def test_unnecessary_status_code(client_logged):
    url = reverse("users:settings_unnecessary")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_unnecessary_form_save_checked_all(client_logged):
    e1 = ExpenseTypeFactory(title="X")
    e2 = ExpenseTypeFactory(title="Y")

    data = {"savings": True, "choices": {e1.pk, e2.pk}}
    url = reverse("users:settings_unnecessary")
    client_logged.post(url, data)

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == "[1, 2]"
    assert actual.unnecessary_savings


# -------------------------------------------------------------------------------------
#                                                                       Journal Settings
# -------------------------------------------------------------------------------------
def test_journal_settings_func():
    view = resolve("/settings/journal/")

    assert views.SettingsJournal == view.func.view_class


def test_journal_settings_status_code(client_logged):
    url = reverse("users:settings_journal")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_journal_settings_form_save(client_logged):
    data = {"lang": "lt", "title": "xxx"}

    url = reverse("users:settings_journal")
    client_logged.post(url, data)

    actual = Journal.objects.first()
    assert actual.lang == "lt"
    assert actual.title == "xxx"
