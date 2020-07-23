import json
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from ...core.tests.utils import change_profile_year
from ...users.factories import UserFactory
from .. import views
from ..factories import DrinkFactory, DrinkTargetFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


#
# ----------------------------------------------------------------------------
#                                                    DrinkTarget create/update
# ----------------------------------------------------------------------------
#
@freeze_time('2000-01-01')
def test_view_drinks(client_logged):
    url = reverse('drinks:drinks_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


def test_view_drinks_new(client_logged):
    data = {'date': '1999-01-01', 'quantity': 999}

    url = reverse('drinks:drinks_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


def test_view_drinks_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse('drinks:drinks_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_view_drinks_update(client_logged):
    p = DrinkFactory()

    data = {'date': '1999-01-01', 'quantity': 999}
    url = reverse('drinks:drinks_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


#
# ----------------------------------------------------------------------------
#                                                    DrinkTarget create/update
# ----------------------------------------------------------------------------
#
def test_view_drinks_target(client_logged):
    url = reverse('drinks:drinks_target_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


def test_view_drinks_target_new(client_logged):
    data = {'year': 1999, 'quantity': 999}

    url = reverse('drinks:drinks_target_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


def test_view_drinks_target_new_invalid_data(client_logged):
    data = {'year': -2, 'quantity': 'x'}

    url = reverse('drinks:drinks_target_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_view_drinks_target_update(get_user, client_logged):
    p = DrinkTargetFactory()

    data = {'year': 1999, 'quantity': 999}
    url = reverse('drinks:drinks_target_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


def test_view_index_func():
    view = resolve('/drinks/')

    assert views.Index == view.func.view_class


def test_view_index_200(client_logged):
    response = client_logged.get('/drinks/')

    assert response.status_code == 200

    assert 'drinks_list' in response.context
    assert 'target_list' in response.context
    assert 'chart_quantity' in response.context
    assert 'chart_consumsion' in response.context
    assert 'tbl_consumsion' in response.context
    assert 'tbl_last_day' in response.context
    assert 'tbl_alcohol' in response.context
    assert 'tbl_std_av' in response.context


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_view_index_drinked_date(client_logged):
    DrinkFactory(date=date(1999, 1, 2))
    DrinkFactory(date=date(1998, 1, 2))

    change_profile_year(client_logged, 1998)

    response = client_logged.get('/drinks/')

    assert '1998-01-02' in response.context["tbl_last_day"]


def test_view_index_drinked_date_empty_db(client_logged):
    response = client_logged.get('/drinks/')

    assert 'Nėra duomenų' in response.context["tbl_last_day"]


def test_view_index_target_empty_db(client_logged):
    response = client_logged.get('/drinks/')

    assert 'Neįvestas tikslas' in response.context["target_list"]


def test_view_index_drinks_list_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    response = client_logged.get('/drinks/')

    assert '<b>1999</b> metais įrašų nėra.' in response.context["drinks_list"]


def test_view_index_tbl_consumsion_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    response = client_logged.get('/drinks/')

    assert 'Nėra duomenų' in response.context["tbl_consumsion"]


def test_view_index_tbl_std_av_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    response = client_logged.get('/drinks/')

    assert 'Nėra duomenų' in response.context["tbl_std_av"]


# ---------------------------------------------------------------------------------------
#                                                                         Hystorical Data
# ---------------------------------------------------------------------------------------
def test_historical_data_func():
    view = resolve('/drinks/historical_data/1/')

    assert views.historical_data is view.func


def test_historical_data_200(client_logged):
    response = client_logged.get('/drinks/historical_data/1/')

    assert response.status_code == 200


def test_historical_data_404(client_logged):
    response = client_logged.get('/drinks/historical_data/x/')

    assert response.status_code == 404


def test_historical_data_302(client):
    url = reverse('drinks:historical_data', kwargs={'qty': '1'})
    response = client.get(url)

    assert response.status_code == 302


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_historical_data_ajax(client_logged):
    DrinkFactory()

    url = reverse('drinks:historical_data', kwargs={'qty': '1'})
    response = client_logged.get(url, {}, **X_Req)

    actual = json.loads(response.content)

    assert response.status_code == 200
    assert "'name': 1999" in actual['html']
    assert "'data': [16.129032258064516, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]" in actual['html']


# ---------------------------------------------------------------------------------------
#                                                                   Filtered Compare Data
# ---------------------------------------------------------------------------------------
@pytest.fixture()
def _compare_form_data():
    return ([
        {"name":"csrfmiddlewaretoken", "value":"RIFWoIjFMOnqjK9mbzZdjeJYucGzet4hcimTmCRnsIw0MTV7eyjvdxFK6FriXrDy"},
        {"name":"year1", "value":"1999"},
        {"name":"year2", "value":"2020"}
    ])


def test_view_compare_func():
    view = resolve('/drinks/compare/')

    assert views.compare is view.func


def test_view_compare_200(client_logged, _compare_form_data):
    form_data = json.dumps(_compare_form_data)
    response = client_logged.post('/drinks/compare/', {'form_data': form_data})

    assert response.status_code == 200


def test_view_compare_404(client_logged):
    response = client_logged.post('/drinks/compare/')

    assert response.status_code == 404


def test_view_compare_500(client_logged):
    form_data = json.dumps([{'x': 'y'}])
    response = client_logged.post('/drinks/compare/', {'form_data': form_data})

    assert response.status_code == 500


def test_view_compare_bad_json_data(client_logged):
    form_data = "{'x': 'y'}"
    response = client_logged.post('/drinks/compare/', {'form_data': form_data})

    assert response.status_code == 500


def test_view_compare_302(client):
    url = reverse('drinks:compare')
    response = client.post(url)

    assert response.status_code == 302


def test_view_compare_form_is_not_valid(client_logged, _compare_form_data):
    _compare_form_data[1]['value'] = None # year1 = None
    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert not actual['form_is_valid']


def test_view_compare_form_is_valid(client_logged, _compare_form_data):
    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert actual['form_is_valid']


def test_view_compare_no_records_for_year(client_logged, _compare_form_data):
    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert 'Trūksta duomenų' in actual['html']


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_view_compare_chart_data(client_logged, _compare_form_data):
    DrinkFactory()
    DrinkFactory(date=date(2020, 1, 1), quantity=10)

    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert response.status_code == 200

    assert "'name': '1999'" in actual['html']
    assert "'data': [16.129032258064516, 0.0" in actual['html']

    assert "'name': '2020'" in actual['html']
    assert "'data': [161.29032258064515, 0.0" in actual['html']


# ---------------------------------------------------------------------------------------
#                                                                            Realod Stats
# ---------------------------------------------------------------------------------------
def test_view_reload_stats_func():
    view = resolve('/drinks/reload_stats/')

    assert views.reload_stats is view.func


def test_view_reload_stats_render(get_user, rf):
    request = rf.get('/drinks/reload_stats/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.reload_stats(request)

    assert response.status_code == 200


def test_view_reload_stats_render_ajax_trigger(client_logged):
    url = reverse('drinks:reload_stats')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200


def test_view_reload_stats_render_ajax_trigger_not_set(client_logged):
    url = reverse('drinks:reload_stats')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class
