import json

import pytest
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseTypeFactory
from ...journals.factories import JournalFactory
from ...journals.models import Journal
from ...users.factories import User, UserFactory
from .. import views

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                Settings
# ---------------------------------------------------------------------------------------
def test_settings_user_must_logged(client):
    url = reverse('users:settings_index')

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'login'


def test_settings_link_if_user_is_superuser(client_logged):
    url = reverse('bookkeeping:index')

    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('users:settings_index')

    assert link in content


def test_settings_no_link_ordinary_user(get_user, client_logged):
    get_user.is_superuser = False
    get_user.save()

    url = reverse('bookkeeping:index')

    response = client_logged.get(url)
    content = response.content.decode('utf-8')

    link = reverse('users:settings_index')

    assert link not in content


# ---------------------------------------------------------------------------------------
#                                                                          Settings Index
# ---------------------------------------------------------------------------------------
def test_index_func():
    view = resolve('/settings/')

    assert views.SettingsIndex == view.func.view_class


def test_index_user_must_be_superuser(get_user, client_logged):
    get_user.is_superuser = False
    get_user.save()

    url = reverse('users:settings_index')

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.url_name == 'index'


def test_index_status_code(client_logged):
    url = reverse('users:settings_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_context(client_logged):
    url = reverse('users:settings_index')
    response = client_logged.get(url)

    assert 'users' in response.context
    assert 'unnecessary' in response.context


# ---------------------------------------------------------------------------------------
#                                                                          Settings Users
# ---------------------------------------------------------------------------------------
def test_users_func():
    view = resolve('/settings/users/')

    assert views.SettingsUsers == view.func.view_class


def test_users_status_code(client_logged):
    url = reverse('users:settings_users')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_users_no_additional_users(client_logged):
    url = reverse('users:settings_users')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert 'There are no additional users.' in actual


def test_users_one_additional_user(get_user, client_logged):
    UserFactory(username='X', is_superuser=False, journal=get_user.journal)
    UserFactory(username='Y', journal=JournalFactory(title='YY'))

    url = reverse('users:settings_users')
    response = client_logged.get(url)
    actual = response.context['items']

    assert Journal.objects.all().count() == 2
    assert User.objects.all().count() == 3
    assert len(actual) == 1


def test_users_delete_func():
    view = resolve('/settings/users/delete/1/')

    assert views.SettingsUsersDelete is view.func.view_class


def test_users_delete_status_200(get_user, client_logged):
    url = reverse('users:settings_users_delete', kwargs={'pk': get_user.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_users_delete_load_form(get_user, client_logged):
    u1 = UserFactory(username='X', journal=get_user.journal)

    url = reverse('users:settings_users_delete', kwargs={'pk': u1.pk})
    response = client_logged.get(url, {}, **X_Req)
    actual = json.loads(response.content)['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'data-action="delete"' in actual
    assert 'data-update-container="user_list">' in actual
    assert f'Ar tikrai nori išrinti: <strong>{ u1 }</strong>?' in actual


def test_users_delete(get_user, client_logged):
    u1 = UserFactory(username='X', journal=get_user.journal)

    url = reverse('users:settings_users_delete', kwargs={'pk': u1.pk})
    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200
    assert User.objects.all().count() == 1


def test_users_delete_html_list(get_user, client_logged):
    u1 = UserFactory(username='X', journal=get_user.journal)
    u2 = UserFactory(username='Y', journal=get_user.journal)

    url = reverse('users:settings_users_delete', kwargs={'pk': u1.pk})
    response = client_logged.post(url, {}, **X_Req)
    actual = json.loads(response.content)['html_list']

    assert response.status_code == 200
    assert User.objects.all().count() == 2
    assert actual.count('<tr>') == 1


def test_users_get_cant_delete_self(get_user, client_logged):
    url = reverse('users:settings_users_delete', kwargs={'pk': get_user.pk})
    response = client_logged.get(url, {}, **X_Req)
    actual = json.loads(response.content)['html_form']

    assert response.status_code == 200
    assert User.objects.all().count() == 1
    assert 'You cannot delete yourself.' in actual


def test_users_post_cant_delete_self(get_user, client_logged):
    url = reverse('users:settings_users_delete', kwargs={'pk': get_user.pk})
    response = client_logged.post(url, {}, **X_Req)
    actual = json.loads(response.content)['html_form']

    assert response.status_code == 200
    assert User.objects.all().count() == 1
    assert 'You cannot delete yourself.' in actual


# ---------------------------------------------------------------------------------------
#                                                                    Unnecessary Expenses
# ---------------------------------------------------------------------------------------
def test_unnecessary_func():
    view = resolve('/settings/unnecessary/')

    assert views.SettingsUnnecessary == view.func.view_class


def test_unnecessary_status_code(client_logged):
    url = reverse('users:settings_unnecessary')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_unnecessary_form_save_checked_all(client_logged):
    e1 = ExpenseTypeFactory(title='X')
    e2 = ExpenseTypeFactory(title='Y')

    data = {
        'savings': True,
        'choices': {e1.pk, e2.pk}
    }

    url = reverse('users:settings_unnecessary')

    client_logged.post(url, data, **X_Req)

    actual = Journal.objects.first()
    assert actual.unnecessary_expenses == '[1, 2]'
    assert actual.unnecessary_savings
