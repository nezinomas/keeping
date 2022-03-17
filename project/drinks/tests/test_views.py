import json
import re
from datetime import date

import pytest
from django.http import JsonResponse
from django.urls import resolve, reverse
from freezegun import freeze_time
from mock import patch

from ...core.tests.utils import change_profile_year, setup_view
from ...journals.factories import JournalFactory
from ...users.factories import User, UserFactory
from .. import models, views
from ..factories import Drink, DrinkFactory, DrinkTargetFactory

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                           Create/Update
# ---------------------------------------------------------------------------------------
@freeze_time('2000-01-01')
def test_new_200(client_logged):
    url = reverse('drinks:drinks_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']


def test_new(client_logged):
    data = {'date': '1999-01-01', 'quantity': 19, 'option': 'beer'}

    url = reverse('drinks:drinks_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '19' in actual['html_list']
    assert '<a role="button" data-url="/drinks/update/1/"' in actual['html_list']


def test_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse('drinks:drinks_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


def test_update(client_logged):
    p = DrinkFactory()

    data = {'date': '1999-01-01', 'quantity': 0.68, 'option': 'beer'}
    url = reverse('drinks:drinks_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '0,68' in actual['html_list']
    assert f'<a role="button" data-url="/drinks/update/{p.pk}/"' in actual['html_list']


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 1.0),
        ('wine', 1.0),
        ('vodka', 1.0),
    ]
)
def test_update_load_form_convert_quantity(drink_type, expect, client_logged):
    p = DrinkFactory(quantity=1, option=drink_type)

    url = reverse('drinks:drinks_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)['html_form']

    assert f'name="quantity" value="{expect}"' in actual


@patch('project.drinks.forms.App_name', 'Counter Type')
def test_drinks_update_not_load_other_user(client_logged, second_user):
    DrinkFactory()
    obj = DrinkFactory(date=date(1111, 1, 1), quantity=0.666, user=second_user)

    url = reverse('drinks:drinks_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert str(obj.quantity) not in form
    assert str(obj.date) not in form


# ---------------------------------------------------------------------------------------
#                                                                            Drink Delete
# ---------------------------------------------------------------------------------------
def test_view_drinks_delete_func():
    view = resolve('/drinks/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_drinks_delete_200(client_logged):
    p = DrinkFactory()

    url = reverse('drinks:drinks_delete', kwargs={'pk': p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_drinks_delete_load_form(client_logged):
    p = DrinkFactory()

    url = reverse('drinks:drinks_delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>1999-01-01: 1.0</strong>?' in actual


def test_view_drinks_delete(client_logged):
    p = DrinkFactory()

    assert models.Drink.objects.all().count() == 1
    url = reverse('drinks:drinks_delete', kwargs={'pk': p.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert models.Drink.objects.all().count() == 0


def test_drinks_delete_other_user_get_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse('drinks:drinks_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert 'SRSLY' in form


def test_drinks_delete_other_user_post_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse('drinks:drinks_delete', kwargs={'pk': obj.pk})
    client_logged.post(url, **X_Req)

    assert models.Drink.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                    Target Create/Update
# ---------------------------------------------------------------------------------------
def test_target(client_logged):
    url = reverse('drinks:drinks_target_new')

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual['html_form']


@pytest.mark.parametrize(
    'type, ml, expect',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 66, 66),
    ]
)
def test_target_new(type, ml, expect, client_logged):
    data = {'year': 1999, 'quantity': ml, 'drink_type': type}

    url = reverse('drinks:drinks_target_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.DrinkTarget.objects.last()
    assert actual.drink_type == type
    assert actual.quantity == expect


def test_target_new_invalid_data(client_logged):
    data = {'year': -2, 'quantity': 'x'}

    url = reverse('drinks:drinks_target_new')

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 500.0),
        ('wine', 750.0),
        ('vodka', 1000.0),
        ('stdav', 1.0),
    ]
)
def test_target_update_load_form_convert_quantity(drink_type, expect, client_logged):
    p = DrinkTargetFactory(quantity=expect, drink_type=drink_type)

    url = reverse('drinks:drinks_target_update', kwargs={'pk': p.pk})

    response = client_logged.get(url, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)['html_form']

    assert f'name="quantity" value="{expect}"' in actual


@pytest.mark.parametrize(
    'type, ml, expect',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 66, 66),
    ]
)
def test_target_update(type, ml, expect, client_logged):
    p = DrinkTargetFactory()

    data = {'year': 1999, 'quantity': ml, 'drink_type': type}
    url = reverse('drinks:drinks_target_update', kwargs={'pk': p.pk})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']

    actual = models.DrinkTarget.objects.get(pk=p.pk)
    assert actual.quantity == expect


@pytest.mark.parametrize(
    'user_drink_type, drink_type, ml, expect_ml, expect_pcs',
    [
        ('beer', 'beer', 500, '500,0', '365'),
        ('wine', 'beer', 500, '234,4', '114'),
        ('vodka', 'beer', 500, '62,5', '23'),
        ('beer', 'wine', 750, '1.600,0', '1.168'),
        ('wine', 'wine', 750, '750,0', '365'),
        ('vodka', 'wine', 750, '200,0', '73'),
        ('beer', 'vodka', 1000, '8.000,0', '5.840'),
        ('wine', 'vodka', 1000, '3.750,0', '1.825'),
        ('vodka', 'vodka', 1000, '1.000,0', '365'),
    ]
)
def test_target_lists(user_drink_type, drink_type, ml, expect_ml, expect_pcs, get_user, client_logged):
    get_user.drink_type = user_drink_type

    p = DrinkTargetFactory(drink_type=drink_type, quantity=ml)

    url = reverse('drinks:drinks_target_lists')

    response = client_logged.get(url, **X_Req)
    actual = response.content.decode('utf-8')

    assert f'<td>{expect_ml}</td>' in actual
    assert f'<td>{expect_pcs}</td>' in actual


def test_target_update_not_load_other_user(client_logged, second_user):
    DrinkTargetFactory()
    obj = DrinkTargetFactory(quantity=666, user=second_user)

    url = reverse('drinks:drinks_target_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert str(obj.quantity) not in form


def test_target_empty_db(client_logged):
    response = client_logged.get('/drinks/')

    assert 'Neįvestas tikslas' in response.context["target_list"]


# ---------------------------------------------------------------------------------------
#                                                                         Historical Data
# ---------------------------------------------------------------------------------------
def test_historical_data_func():
    view = resolve('/drinks/historical_data/1/')

    assert views.HistoricalData is view.func.view_class


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
        {"name":"csrfmiddlewaretoken", "value":"xxx"},
        {"name":"year1", "value":"1999"},
        {"name":"year2", "value":"2020"}
    ])


def test_compare_func():
    view = resolve('/drinks/compare/')

    assert views.Compare is view.func.view_class


def test_compare_200(client_logged, _compare_form_data):
    form_data = json.dumps(_compare_form_data)
    response = client_logged.post('/drinks/compare/', {'form_data': form_data})

    assert response.status_code == 200


def test_compare_404(client_logged):
    response = client_logged.post('/drinks/compare/')

    assert response.status_code == 404


def test_compare_500(client_logged):
    form_data = json.dumps([{'x': 'y'}])
    response = client_logged.post('/drinks/compare/', {'form_data': form_data})

    assert response.status_code == 500


def test_compare_bad_json_data(client_logged):
    form_data = "{'x': 'y'}"
    response = client_logged.post('/drinks/compare/', {'form_data': form_data})

    assert response.status_code == 500


def test_compare_302(client):
    url = reverse('drinks:compare')
    response = client.post(url)

    assert response.status_code == 302


def test_compare_form_is_not_valid(client_logged, _compare_form_data):
    _compare_form_data[1]['value'] = None  # year1 = None
    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert not actual['form_is_valid']


def test_compare_form_is_valid(client_logged, _compare_form_data):
    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert actual['form_is_valid']


def test_compare_no_records_for_year(client_logged, _compare_form_data):
    form_data = json.dumps(_compare_form_data)

    url = reverse('drinks:compare')
    response = client_logged.post(url, {'form_data': form_data})

    actual = json.loads(response.content)

    assert 'Nėra duomenų' in actual['html']


def test_compare_chart_data(client_logged, _compare_form_data):
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
def test_reload_stats_func():
    view = resolve('/drinks/reload_stats/')

    assert views.ReloadStats is view.func.view_class


def test_reload_stats_render_ajax_trigger(client_logged):
    url = reverse('drinks:reload_stats')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200
    assert views.ReloadStats == response.resolver_match.func.view_class

    actual = json.loads(response.content)

    assert 'chart_consumption' in actual
    assert 'chart_quantity' in actual
    assert 'tbl_consumption' in actual
    assert 'tbl_last_day' in actual
    assert 'tbl_alcohol' in actual
    assert 'tbl_std_av' in actual
    assert 'target_list' in actual


def test_reload_stats_response_type(client_logged):
    url = reverse('drinks:reload_stats')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert isinstance(response, JsonResponse)


def test_reload_stats_render_ajax_trigger_not_set(client_logged):
    url = reverse('drinks:reload_stats')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


# ---------------------------------------------------------------------------------------
#                                                                              IndexView
# ---------------------------------------------------------------------------------------
def test_index_func():
    view = resolve('/drinks/')

    assert views.Index == view.func.view_class


def test_index_200(client_logged):
    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_add_button(client_logged):
    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<button type="button" class="btn.+data-url="(.*?)".+ (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse('drinks:drinks_new')
    assert res[0][1] == 'Gertynės'


def test_index_links(client_logged):
    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<a href="(.*?)" class="btn btn-sm.+>(\w+)<\/a>')
    res = re.findall(pattern, content)

    assert len(res) == 3
    assert res[0][0] == reverse('drinks:drinks_index')
    assert res[0][1] == 'Grafikai'

    assert res[1][0] == reverse('drinks:drinks_list')
    assert res[1][1] == 'Duomenys'

    assert res[2][0] == reverse('drinks:drinks_history')
    assert res[2][1] == 'Istorija'


def test_index_context(client_logged):
    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    assert 'tab' in response.context
    assert 'chart_quantity' in response.context
    assert 'chart_consumption' in response.context
    assert 'tbl_consumption' in response.context
    assert 'tbl_last_day' in response.context
    assert 'tbl_alcohol' in response.context
    assert 'tbl_std_av' in response.context
    assert 'target_list' in response.context
    assert 'all_years' in response.context
    assert 'compare_form' in response.context
    assert 'select_drink_type' in response.context


def test_index_context_tab_value(client_logged):
    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    assert response.context['tab'] == 'index'

@freeze_time('1999-1-1')
def test_index_chart_consumption(client_logged):
    DrinkFactory()

    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")
    content = content.replace('\n', '')

    assert 'id="chart_consumption"><div id="chart_consumption_container"></div>' in content


@freeze_time('1999-1-1')
def test_index_chart_quantity(client_logged):
    DrinkFactory()

    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")
    content = content.replace('\n', '')

    assert 'id="chart_quantity"><div id="chart_quantity_container"></div>' in content


def test_index_drinked_date(client_logged):
    DrinkFactory(date=date(1999, 1, 2))
    DrinkFactory(date=date(1998, 1, 2))

    change_profile_year(client_logged, 1998)

    response = client_logged.get('/drinks/')

    assert '1998-01-02' in response.context["tbl_last_day"]


def test_index_drinked_date_empty_db(client_logged):
    response = client_logged.get('/drinks/')

    assert 'Nėra duomenų' in response.context["tbl_last_day"]


def test_index_tbl_consumption_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    response = client_logged.get('/drinks/')

    assert 'Nėra duomenų' in response.context["tbl_consumption"]


@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', 'Avg: 14'),
        ('beer', 'wine', 'Avg: 44'),
        ('beer', 'vodka', 'Avg: 219'),
    ]
)
def test_chart_consumption_avg(user_drink_type, drink_type, expect, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkFactory(quantity=10, option=drink_type)

    response = client_logged.get('/drinks/')
    actual = response.context["chart_consumption"]

    assert expect in actual


@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', 'Riba: 500'),
        ('beer', 'wine', 'Riba: 1.067'),
        ('beer', 'vodka', 'Riba: 4.000'),
    ]
)
def test_chart_consumption_limit(user_drink_type, drink_type, expect, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkTargetFactory(quantity=500, drink_type=drink_type)

    response = client_logged.get('/drinks/')
    actual = response.context["chart_consumption"]

    assert expect in actual


def test_index_tbl_std_av_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    response = client_logged.get('/drinks/')

    assert 'Nėra duomenų' in response.context["tbl_std_av"]


@freeze_time('1999-1-1')
def test_index_first_record_with_gap_from_previous_year(client_logged):
    DrinkFactory(date=date(1999, 1, 2))
    DrinkFactory(date=date(1998, 1, 1))

    response = client_logged.get('/drinks/')
    context = response.context

    assert "'1999-01-02', 1.0, 366.0]" in context['chart_calendar_1H']


@freeze_time('1999-1-1')
def test_index_no_data_dry_days(client_logged):
    DrinkFactory(date=date(1998, 1, 1))

    response = client_logged.get('/drinks/')
    context = response.context

    assert "1998-01-01" in context['tbl_last_day']
    assert "365" in context['tbl_last_day']


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 'Alus'),
        ('wine', 'Vynas'),
        ('vodka', 'Degtinė'),
        ('stdav', 'Std Av'),
    ]
)
def test_index_select_drink_drop_down_title(drink_type, expect, main_user, client_logged):
    main_user.drink_type = drink_type
    main_user.save()

    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    content = response.content.decode('utf-8')

    assert f'id="dropdownDrinkType">{ expect }</a>' in content


def test_index_select_drink_drop_down_link_list(client_logged):
    url = reverse('drinks:drinks_index')
    response = client_logged.get(url)

    content = response.content.decode()

    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "beer"})}">Alus</a>' in content
    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})}">Vynas</a>' in content
    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "vodka"})}">Degtinė</a>' in content
    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "stdav"})}">Std Av</a>' in content


# ---------------------------------------------------------------------------------------
#                                                                                   Lists
# ---------------------------------------------------------------------------------------
def test_list_func():
    view = resolve('/drinks/lists/')

    assert views.Lists == view.func.view_class


def test_list_200(client_logged):
    url = reverse('drinks:drinks_list')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_list_context(client_logged):
    url = reverse('drinks:drinks_list')
    response = client_logged.get(url)

    assert 'items' in response.context
    assert 'tab' in response.context


def test_list_context_tab_value(client_logged):
    url = reverse('drinks:drinks_list')
    response = client_logged.get(url)

    assert response.context['tab'] == 'data'


def test_list_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse('drinks:drinks_list')
    response = client_logged.get(url)

    assert '<b>1999</b> metais įrašų nėra.' in response.content.decode('utf-8')


def test_list(client_logged):
    p = DrinkFactory(quantity=19)
    response = client_logged.get(reverse('drinks:drinks_list'))

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert '19,0' in actual
    assert f'<a role="button" data-url="/drinks/update/{p.pk}/"' in actual


# ---------------------------------------------------------------------------------------
#                                                                                 Summary
# ---------------------------------------------------------------------------------------
def test_history_func():
    view = resolve('/drinks/history/')

    assert views.Summary == view.func.view_class


def test_history_200(client_logged):
    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_history_context_tab_value(client_logged):
    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    assert response.context['tab'] == 'history'


def test_history_context(client_logged):
    DrinkFactory()

    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    assert 'drinks_categories' in response.context
    assert 'drinks_data_ml' in response.context
    assert 'drinks_data_alcohol' in response.context


@freeze_time('1999-1-1')
def test_history_chart_consumption(client_logged):
    DrinkFactory()

    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_summary_container"></div>' in content


@freeze_time('1999-01-01')
def test_history_drinks_years(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1998, 1, 1))

    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    assert response.context['drinks_categories'] == [1998, 1999]


@freeze_time('1999-01-01')
@pytest.mark.parametrize(
    'user_drink_type, drink_type, ml',
    [
        ('beer', 'beer', [2.74, 1.37]),
        ('beer', 'wine', [8.77, 4.38]),
        ('beer', 'vodka', [43.84, 21.92]),
    ]
)
def test_history_drinks_data_ml(user_drink_type, drink_type, ml, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkFactory(date=date(1999, 1, 1), quantity=1, option=drink_type)
    DrinkFactory(date=date(1998, 1, 1), quantity=2, option=drink_type)

    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    assert response.context['drinks_data_ml'] == pytest.approx(ml, rel=1e-2)


@freeze_time('1999-01-01')
@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', [0.05, 0.025]),
        ('beer', 'wine', [0.16, 0.08]),
        ('beer', 'vodka', [0.8, 0.4]),
    ]
)
def test_history_drinks_data_alcohol(user_drink_type, drink_type, expect, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkFactory(quantity=1, option=drink_type)
    DrinkFactory(date=date(1998, 1, 1), quantity=2, option=drink_type)

    url = reverse('drinks:drinks_history')
    response = client_logged.get(url)

    assert response.context['drinks_data_alcohol'] == pytest.approx(expect, 0.01)


@freeze_time('1999-1-1')
def test_history_categories_with_empty_year_in_between(fake_request):
    DrinkFactory(date=date(1997, 1, 1), quantity=15)
    DrinkFactory(date=date(1999, 1, 1), quantity=15)
    DrinkFactory(date=date(1999, 1, 1), quantity=15)

    class Dummy(views.Summary):
        pass

    view = setup_view(Dummy(), fake_request)
    actual = view.get_context_data()

    assert actual['drinks_categories'] == [1997, 1998, 1999]
    assert pytest.approx(actual['drinks_data_ml'], 0.01) == [20.55, 0.0, 41.1]
    assert pytest.approx(actual['drinks_data_alcohol'], rel=1e-1) == [0.38, 0.0, 0.75]


@freeze_time('1999-1-1')
@pytest.mark.parametrize(
    'user_drink_type, drink_type, ml, alkohol',
    [
        ('beer', 'beer', [1.37, 0.0], [0.025, 0.0]),
        ('beer', 'wine', [4.38, 0.0], [0.08, 0.0]),
        ('beer', 'vodka', [21.92, 0.0], [0.4, 0.0]),
    ]
)
def test_history_categories_with_empty_current_year(user_drink_type, drink_type, ml, alkohol, get_user, fake_request):
    get_user.drink_type = user_drink_type

    DrinkFactory(date=date(1998, 1, 1), quantity=1, option=drink_type)

    class Dummy(views.Summary):
        pass

    view = setup_view(Dummy(), fake_request)
    actual = view.get_context_data()

    assert actual['drinks_categories'] == [1998, 1999]
    assert pytest.approx(actual['drinks_data_ml'], rel=1e-1) == ml
    assert pytest.approx(actual['drinks_data_alcohol'], rel=1e-1) == alkohol


# ---------------------------------------------------------------------------------------
#                                                                            Select Drink
# ---------------------------------------------------------------------------------------
def test_select_drink_func():
    view = resolve('/drinks/drink_type/xxx/')

    assert views.SelectDrink == view.func.view_class


def test_select_drink_redirect(client_logged):
    url = reverse('drinks:set_drink_type', kwargs={'drink_type': 'xxx'})

    response = client_logged.get(url)

    assert response.status_code == 302


def test_select_drink_redirect_follow(client_logged):
    url = reverse('drinks:set_drink_type', kwargs={'drink_type': 'xxx'})

    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


def test_select_drinks_set_drink_type(client_logged):
    url = reverse('drinks:set_drink_type', kwargs={'drink_type': 'wine'})

    response = client_logged.get(url)

    actual = User.objects.first()

    assert actual.drink_type == 'wine'


def test_select_drinks_set_default_drink_type(main_user, client_logged):
    main_user.drink_type = 'wine'
    main_user.save()

    assert User.objects.first().drink_type == 'wine'

    url = reverse('drinks:set_drink_type', kwargs={'drink_type': 'xxx'})

    response = client_logged.get(url)

    actual = User.objects.first()

    assert actual.drink_type == 'beer'
