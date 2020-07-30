import json
import re

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from ...users.factories import UserFactory
from .. import views
from ..factories import NightFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                         Nights create/update
# ----------------------------------------------------------------------------
@freeze_time('2000-01-01')
def test_view_nights(client_logged):
    url = reverse('nights:nights_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


def test_view_nights_new(client_logged):
    data = {'date': '1999-01-01', 'quantity': 999}

    url = reverse('nights:nights_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


def test_view_nights_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse('nights:nights_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_view_nights_update(client_logged):
    p = NightFactory()

    data = {'date': '1999-01-01', 'quantity': 999}
    url = reverse('nights:nights_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '999' in actual['html_list']


# ----------------------------------------------------------------------------
#                                                             Nights IndexView
# ----------------------------------------------------------------------------
def test_nights_index_func():
    view = resolve('/nights/')

    assert views.Index == view.func.view_class


def test_nights_index_200(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_nights_index_add_button(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<button type="button".+data-url="(.*?)".+ (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse('nights:nights_new')
    assert res[0][1] == 'Pridėti'


def test_nights_index_links(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<a href="(.*?)" class="btn btn-sm.+>(\w+)<\/a>')
    res = re.findall(pattern, content)

    assert len(res) == 3
    assert res[0][0] == reverse('nights:nights_index')
    assert res[0][1] == 'Grafikai'

    assert res[1][0] == reverse('nights:nights_list')
    assert res[1][1] == 'Duomenys'

    assert res[2][0] == reverse('nights:nights_history')
    assert res[2][1] == 'Istorija'


def test_nigths_index_context(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context
    assert 'chart_months' in response.context
    assert 'chart_year' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context


def test_nigths_index_context_tab_value(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert response.context['tab'] == 'index'


def test_nights_index_chart_weekdays(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_weekdays"><div id="chart_weekdays_container"></div>' in content


def test_nights_index_chart_months(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_months"><div id="chart_months_container"></div>' in content


def test_nights_index_charts_of_year(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    for i in range(1, 13):
        assert f'<div id="chart_m{i}_container"></div>' in content


@freeze_time('1999-07-18')
@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_nigths_index_info_row(client_logged):
    NightFactory(quantity=3)

    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    pattern = re.compile(r'Kiek:.+(\d+).+Savaitė.+(\d+).+Per savaitę.+([\d,]+)')

    for m in re.finditer(pattern, content):
        assert m.group(1) == 3
        assert m.group(2) == 28
        assert m.group(3) == '0,1'


# ---------------------------------------------------------------------------------------
#                                                                            Realod Stats
# ---------------------------------------------------------------------------------------
def test_night_reload_stats_func():
    view = resolve('/nights/reload_stats/')

    assert views.reload_stats is view.func


def test_night_reload_stats_render(get_user, rf):
    request = rf.get('/nights/reload_stats/?ajax_trigger=1')
    request.user = UserFactory.build()

    response = views.reload_stats(request)

    assert response.status_code == 200


def test_night_reload_stats_render_ajax_trigger(client_logged):
    url = reverse('nights:reload_stats')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200


def test_night_reload_stats_render_ajax_trigger_not_set(client_logged):
    url = reverse('nights:reload_stats')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


# ----------------------------------------------------------------------------
#                                                                  Nights Lists
# ----------------------------------------------------------------------------
def test_nights_list_func():
    view = resolve('/nights/lists/')

    assert views.Lists == view.func.view_class


def test_nights_list_200(client_logged):
    url = reverse('nights:nights_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_nigths_list_context(client_logged):
    url = reverse('nights:nights_list')
    response = client_logged.get(url)

    assert 'data' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context


def test_nigths_list_context_tab_value(client_logged):
    url = reverse('nights:nights_list')
    response = client_logged.get(url)

    assert response.context['tab'] == 'data'


# ----------------------------------------------------------------------------
#                                                               Nights History
# ----------------------------------------------------------------------------
def test_nights_history_func():
    view = resolve('/nights/history/')

    assert views.History == view.func.view_class


def test_nights_history_200(client_logged):
    url = reverse('nights:nights_history')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_nigths_history_context(client_logged):
    url = reverse('nights:nights_history')
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context
    assert 'chart_years' in response.context
    assert 'tab' in response.context


def test_nights_history_chart_weekdays(client_logged):
    url = reverse('nights:nights_history')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_weekdays_container"></div>' in content


def test_nights_history_chart_years(client_logged):
    url = reverse('nights:nights_history')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_years_container"></div>' in content
