import json

import pandas  # need to import before freezegun, why?
import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...core.factories import UserFactory
from .. import views
from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


#
#         DrinkTarget create/update
#
@freeze_time('1999-01-01')
def test_view_drinks(admin_client):
    url = reverse('drinks:drinks_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


@pytest.mark.django_db()
def test_view_drinks_new(client, login):
    data = {'date': '1999-01-01', 'quantity': 999}

    url = reverse('drinks:drinks_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


@pytest.mark.django_db()
def test_view_drinks_new_invalid_data(client, login):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse('drinks:drinks_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_drinks_update(client, login):
    p = DrinkFactory()

    data = {'date': '1999-01-01', 'quantity': 999}
    url = reverse('drinks:drinks_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


#
#         DrinkTarget create/update
#
@freeze_time('1999-01-01')
def test_view_drinks_target(admin_client):
    url = reverse('drinks:drinks_target_new')

    response = admin_client.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert 200 == response.status_code
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.django_db()
def test_view_drinks_target_new(client, login):
    data = {'year': 1999, 'quantity': 999}

    url = reverse('drinks:drinks_target_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


@pytest.mark.django_db()
def test_view_drinks_target_new_invalid_data(client, login):
    data = {'year': -2, 'quantity': 'x'}

    url = reverse('drinks:drinks_target_new')

    response = client.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.django_db()
def test_view_drinks_target_update(client, login):
    p = DrinkTargetFactory()

    data = {'year': 1999, 'quantity': 999}
    url = reverse('drinks:drinks_target_update', kwargs={'pk': p.pk})

    response = client.post(url, data, **X_Req)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


def test_view_index_func():
    view = resolve('/drinks/')

    assert views.Index == view.func.view_class


def test_view_reload_stats_func():
    view = resolve('/drinks/reload_stats/')

    assert views.reload_stats == view.func


@pytest.mark.django_db
def test_view_reload_stats_render(rf):
    request = rf.get('/drinks/reload_stats/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.reload_stats(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_view_index_200(login, client):
    response = client.get('/drinks/')

    assert response.status_code == 200

    assert 'drinks_list' in response.context
    assert 'target_list' in response.context
    assert 'chart_quantity' in response.context
    assert 'chart_consumsion' in response.context
    assert 'tbl_consumsion' in response.context
    assert 'tbl_last_day' in response.context
    assert 'tbl_alcohol' in response.context
    assert 'tbl_std_av' in response.context
