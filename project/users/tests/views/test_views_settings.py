import pytest
from django.urls import reverse

from ....expenses.tests.factories import ExpenseTypeFactory
from ....journals.models import Journal
from ....journals.tests.factories import JournalFactory
from ..factories import User, UserFactory

pytestmark = pytest.mark.django_db


def test_index_renders_its_three_sections(client_logged):
    url = reverse("users:settings_index")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert f'hx-post="{reverse("users:settings_journal")}"' in content
    assert f'hx-post="{reverse("users:settings_unnecessary")}"' in content
    assert "Nėra papildomų vartotojų." in content


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


def test_users_delete_load_form(main_user, client_logged):
    u1 = UserFactory(username="X", email="x@x.x", journal=main_user.journal)

    url = reverse("users:settings_users_delete", kwargs={"pk": u1.pk})
    response = client_logged.get(url, {})
    actual = response.content.decode()

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
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
    client_logged.post(url)

    assert User.objects.all().count() == 1


def test_unnecessary_page_renders_its_form(client_logged):
    url = reverse("users:settings_unnecessary")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'hx-post="{url}"' in content
    assert 'name="savings"' in content


def test_unnecessary_form_save_checked_all(client_logged):
    e1 = ExpenseTypeFactory(title="X")
    e2 = ExpenseTypeFactory(title="Y")

    data = {"savings": True, "choices": {e1.pk, e2.pk}}
    url = reverse("users:settings_unnecessary")
    client_logged.post(url, data)

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == f"[{e1.pk}, {e2.pk}]"
    assert actual.unnecessary_savings


def test_journal_settings_status_code(client_logged):
    url = reverse("users:settings_journal")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'hx-post="{url}"' in content
    assert 'name="title"' in content
    assert 'name="lang"' in content


def test_journal_settings_form_save(client_logged):
    data = {"lang": "lt", "title": "xxx"}

    url = reverse("users:settings_journal")
    client_logged.post(url, data)

    actual = Journal.objects.first()
    assert actual.lang == "lt"
    assert actual.title == "xxx"
