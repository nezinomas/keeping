import json
import re

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from .. import views
from ..apps import App_name
from ..factories import NightFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                           Create/Update View
# ----------------------------------------------------------------------------
@freeze_time('2000-01-01')
def test_view_new_form_initial(client_logged):
    url = reverse(f'{App_name}:{App_name}_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']
    assert '<input type="number" name="quantity" value="1"' in actual['html_form']


@patch(f'project.{App_name}.models.NightQuerySet.App_name', 'Counter Type')
@patch(f'project.{App_name}.forms.App_name', 'Counter Type')
def test_view_new(client_logged):
    data = {'date': '1999-01-01', 'quantity': 68}

    url = reverse(f'{App_name}:{App_name}_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '68' in actual['html_list']
    assert f'<a type="button" data-url="/{App_name}/update/1/"' in actual['html_list']


def test_view_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse(f'{App_name}:{App_name}_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@patch(f'project.{App_name}.models.NightQuerySet.App_name', 'Counter Type')
@patch(f'project.{App_name}.forms.App_name', 'Counter Type')
def test_view_update(client_logged):
    p = NightFactory()

    data = {'date': '1999-01-01', 'quantity': 68}
    url = reverse(f'{App_name}:{App_name}_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '68' in actual['html_list']
    assert f'<a type="button" data-url="/{App_name}/update/{p.pk}/"' in actual['html_list']


# ----------------------------------------------------------------------------
#                                                                   Index View
# ----------------------------------------------------------------------------
def test_index_func():
    view = resolve(f'/{App_name}/')

    assert views.Index == view.func.view_class


def test_index_200(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_add_button(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<button type="button".+data-url="(.*?)".+ (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse(f'{App_name}:{App_name}_new')
    assert res[0][1] == 'Pridėti'


def test_index_links(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<a href="(.*?)" class="btn btn-sm.+>(\w+)<\/a>')
    res = re.findall(pattern, content)

    assert len(res) == 3
    assert res[0][0] == reverse(f'{App_name}:{App_name}_index')
    assert res[0][1] == 'Grafikai'

    assert res[1][0] == reverse(f'{App_name}:{App_name}_list')
    assert res[1][1] == 'Duomenys'

    assert res[2][0] == reverse(f'{App_name}:{App_name}_history')
    assert res[2][1] == 'Istorija'


def test_index_context(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context
    assert 'chart_months' in response.context
    assert 'chart_year' in response.context
    assert 'chart_histogram' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context


def test_index_context_tab_value(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    assert response.context['tab'] == 'index'


def test_index_chart_weekdays(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_weekdays"><div id="chart_weekdays_container"></div>' in content


def test_index_chart_months(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_months"><div id="chart_months_container"></div>' in content


def test_index_chart_histogram(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_histogram"><div id="chart_histogram_container"></div>' in content


def test_index_charts_of_year(client_logged):
    url = reverse(f'{App_name}:{App_name}_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    for i in range(1, 13):
        assert f'<div id="chart_m{i}_container"></div>' in content


@freeze_time('1999-07-18')
@patch(f'project.{App_name}.models.NightQuerySet.App_name', 'Counter Type')
def test_index_info_row(client_logged):
    NightFactory(quantity=3)

    url = reverse(f'{App_name}:{App_name}_index')
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
def test_reload_stats_func():
    view = resolve(f'/{App_name}/reload_stats/')

    assert views.ReloadStats == view.func.view_class


def test_reload_stats_render_ajax_trigger(client_logged):
    url = reverse(f'{App_name}:reload_stats')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200
    assert views.ReloadStats == response.resolver_match.func.view_class



def test_reload_stats_render_ajax_trigger_not_set(client_logged):
    url = reverse(f'{App_name}:reload_stats')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


# ----------------------------------------------------------------------------
#                                                                    List View
# ----------------------------------------------------------------------------
def test_list_func():
    view = resolve(f'/{App_name}/lists/')

    assert views.Lists == view.func.view_class


def test_list_200(client_logged):
    url = reverse(f'{App_name}:{App_name}_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_list_context(client_logged):
    url = reverse(f'{App_name}:{App_name}_list')
    response = client_logged.get(url)

    assert 'data' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context


def test_list_context_tab_value(client_logged):
    url = reverse(f'{App_name}:{App_name}_list')
    response = client_logged.get(url)

    assert response.context['tab'] == 'data'


@patch(f'project.{App_name}.models.NightQuerySet.App_name', 'Counter Type')
def test_list(client_logged):
    p = NightFactory(quantity=66)
    url = reverse(f'{App_name}:{App_name}_list')
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert '66' in actual
    assert f'<a type="button" data-url="/{App_name}/update/{p.pk}/"' in actual


@patch(f'project.{App_name}.models.NightQuerySet.App_name', 'Counter Type')
def test_list_empty(client_logged):
    url = reverse(f'{App_name}:{App_name}_list')
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert '<b>1999</b> metais įrašų nėra.' in actual


# ----------------------------------------------------------------------------
#                                                                 History View
# ----------------------------------------------------------------------------
def test_history_func():
    view = resolve(f'/{App_name}/history/')

    assert views.History == view.func.view_class


def test_history_200(client_logged):
    url = reverse(f'{App_name}:{App_name}_history')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_history_context(client_logged):
    url = reverse(f'{App_name}:{App_name}_history')
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context
    assert 'chart_years' in response.context
    assert 'tab' in response.context


def test_history_chart_weekdays(client_logged):
    url = reverse(f'{App_name}:{App_name}_history')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_weekdays_container"></div>' in content


def test_history_chart_years(client_logged):
    url = reverse(f'{App_name}:{App_name}_history')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_years_container"></div>' in content
