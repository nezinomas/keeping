import json
import re
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

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

    content = response.content.decode("utf-8")

    pattern = re.compile(r'\<button type=\"button\".*?url="(.*?)".*? (\w)\<\/button\>')

    for m in re.finditer(pattern, content):
        assert m.group(1) == url
        assert m.group(2) == 'Pridėti'


def test_nights_index_chart_weekdays(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_weekdays"><div id="chart_weekdays_container"></div>' in content


def test_nigths_index_context_chart_weekdays(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context


def test_nights_index_chart_months(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_months"><div id="chart_months_container"></div>' in content


def test_nigths_index_context_chart_months(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert 'chart_months' in response.context


def test_nights_index_charts_of_year(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    for i in range(1, 13):
        assert f'<div id="chart_m{i}_container"></div>' in content


def test_nigths_index_context_charts_of_year(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert 'chart_year' in response.context


def test_nigths_index_context_info_row(client_logged):
    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    assert 'info_row' in response.context


@freeze_time('1999-07-18')
@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_nigths_index_info_row(client_logged):
    NightFactory(quantity=3)

    url = reverse('nights:nights_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'Kiek: 3' in content
    assert 'Savaitė: 28' in content
    assert 'Per savaitę: 0,1' in content
