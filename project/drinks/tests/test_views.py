from requests import request
from ...core.tests.utils import setup_view
import re
from datetime import date

import pytest
from django.urls import resolve, reverse, reverse_lazy
from freezegun import freeze_time

from ...core.tests.utils import change_profile_year, setup_view
from ...users.factories import User
from .. import models, views
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                              IndexView
# ---------------------------------------------------------------------------------------
def test_index_func():
    view = resolve('/drinks/')
    assert views.Index == view.func.view_class


def test_index_200(client_logged):
    url = reverse('drinks:index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_add_button(client_logged):
    url = reverse('drinks:index')
    response = client_logged.get(url)
    content = response.content.decode()
    pattern = re.compile(
        r'<button type="button" id="btn-new" class="btn btn-sm btn-outline-success" hx-get="(.*?)" hx-target="#dialog">.*? (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse('drinks:new', kwargs={'tab': 'index'})
    assert res[0][1] == 'Gertynės'


def test_index_links(client_logged):
    url = reverse('drinks:index')
    response = client_logged.get(url)
    content = response.content.decode()
    content = content.replace('\n', '')
    content = content.replace('           ', '')
    content = content.replace('       ', '')

    pattern = re.compile(
        r'<a role="button".*?hx-get="(.*?)".*?> (\w+) <\/a>')
    res = re.findall(pattern, content)

    assert len(res) == 3
    assert res[0][0] == reverse('drinks:tab_index')
    assert res[0][1] == 'Grafikai'

    assert res[1][0] == reverse('drinks:tab_data')
    assert res[1][1] == 'Duomenys'

    assert res[2][0] == reverse('drinks:tab_history')
    assert res[2][1] == 'Istorija'


def test_index_context(client_logged):
    url = reverse('drinks:index')
    response = client_logged.get(url)
    context = response.context

    assert 'tab_content' in context
    assert 'select_drink_type' in context
    assert 'current_drink_type' in context


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

    url = reverse('drinks:index')
    response = client_logged.get(url)

    content = response.content.decode('utf-8')

    assert f'id="dropdownDrinkType">{ expect }</a>' in content


def test_index_select_drink_drop_down_link_list(client_logged):
    url = reverse('drinks:index')
    response = client_logged.get(url)

    content = response.content.decode()

    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "beer"})}">Alus</a>' in content
    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})}">Vynas</a>' in content
    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "vodka"})}">Degtinė</a>' in content
    assert f'href="{reverse("drinks:set_drink_type", kwargs={"drink_type": "stdav"})}">Std Av</a>' in content


# ---------------------------------------------------------------------------------------
#                                                                           TabIndex View
# ---------------------------------------------------------------------------------------
def test_tab_index_func():
    view = resolve('/drinks/index/')
    assert views.TabIndex == view.func.view_class


def test_tab_index_200(client_logged):
    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_index_context(client_logged):
    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert 'target_list' in response.context
    assert 'compare_form_and_chart' in response.context
    assert 'all_years' in response.context
    assert 'records' in response.context
    assert 'chart_quantity' in response.context
    assert 'chart_consumption' in response.context
    assert 'chart_calendar_1H' in response.context
    assert 'chart_calendar_2H' in response.context
    assert 'tbl_consumption' in response.context
    assert 'tbl_last_day' in response.context
    assert 'tbl_alcohol' in response.context
    assert 'tbl_std_av' in response.context


def test_tab_index_no_recods_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert '<b>1999</b> metais įrašų nėra.' in response.content.decode('utf-8')


@freeze_time('1999-1-1')
def test_tab_index_chart_consumption(client_logged):
    DrinkFactory()

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    content = response.content.decode("utf-8")
    content = content.replace('\n', '')

    assert '<div id="chart-consumption-container"></div>' in content


@freeze_time('1999-1-1')
def test_tab_index_chart_quantity(client_logged):
    DrinkFactory()

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)
    content = response.content.decode("utf-8")
    content = content.replace('\n', '')

    assert '<div id="chart-quantity-container"></div>' in content


def test_tab_index_drinked_date(client_logged):
    DrinkFactory(date=date(1999, 1, 2))
    DrinkFactory(date=date(1998, 1, 2))

    change_profile_year(client_logged, 1998)

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert '1998-01-02' in response.context["tbl_last_day"]


def test_tab_index_drinked_date_empty_db(client_logged):
    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert 'Nėra duomenų' in response.context["tbl_last_day"]


def test_tab_index_tbl_consumption_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert 'Nėra duomenų' in response.context["tbl_consumption"]


@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', 14),
        ('beer', 'wine', 44),
        ('beer', 'vodka', 219),
    ]
)
def test_tab_index_chart_consumption_avg(user_drink_type, drink_type, expect, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkFactory(quantity=10, option=drink_type)

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)
    actual = response.context["chart_consumption"]

    assert expect == round(actual['avg'])


@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', 500),
        ('beer', 'wine', 1067),
        ('beer', 'vodka', 4000),
    ]
)
def test_tab_index_chart_consumption_limit(user_drink_type, drink_type, expect, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkTargetFactory(quantity=500, drink_type=drink_type)

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)
    actual = response.context["chart_consumption"]["target"]

    assert expect == round(actual, 0)


def test_tab_index_tbl_std_av_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)

    assert 'Nėra duomenų' in response.context["tbl_std_av"]


@freeze_time('1999-1-1')
def test_tab_index_first_record_with_gap_from_previous_year(client_logged):
    DrinkFactory(date=date(1999, 1, 2))
    DrinkFactory(date=date(1998, 1, 1))

    url = reverse('drinks:tab_index')
    response = client_logged.get(url)
    context = response.context['chart_calendar_1H']['data'][0]['data']

    assert context[4] == [0, 4, 0.05, 53, '1999-01-01']
    assert context[5] == [0, 5, 1.0, 53, '1999-01-02', 1.0, 366.0]


@freeze_time('1999-1-1')
def test_tab_index_no_data_dry_days(client_logged):
    DrinkFactory(date=date(1998, 1, 1))

    url=reverse('drinks:tab_index')
    response=client_logged.get(url)
    context = response.context

    assert "1998-01-01" in context['tbl_last_day']
    assert "365" in context['tbl_last_day']


@pytest.mark.parametrize(
    'drink_type, qty, expect',
    [
        ('beer', 4, '0,10'),
        ('wine', 1.25, '0,10'),
        ('vodka', 0.25, '0,10'),
        ('stdav', 10, '0,10'),
    ]
)
def test_tab_index_tbl_alcohol(drink_type, qty, expect, get_user, client_logged):
    get_user.drink_type = drink_type

    DrinkFactory(option=drink_type, quantity=qty)

    url = reverse('drinks:index')
    response = client_logged.get(url)
    actual = response.context.get('tbl_alcohol')

    assert f'<td>{expect}</td>' in actual


# ---------------------------------------------------------------------------------------
#                                                                            TabData View
# ---------------------------------------------------------------------------------------
def test_tab_data_func():
    view = resolve('/drinks/data/')

    assert views.TabData == view.func.view_class


def test_tab_data_200(client_logged):
    url = reverse('drinks:tab_data')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_data_context(client_logged):
    url = reverse('drinks:tab_data')
    response = client_logged.get(url)

    assert 'object_list' in response.context


def test_tab_data_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse('drinks:tab_data')
    response = client_logged.get(url)

    assert '<b>1999</b> metais įrašų nėra.' in response.content.decode('utf-8')


def test_tab_data(client_logged):
    p = DrinkFactory(quantity=19)
    response = client_logged.get(reverse('drinks:tab_data'))

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert '19,0' in actual
    assert f'<a role="button" hx-get="/drinks/update/{p.pk}/"' in actual
    assert f'<a role="button" hx-get="/drinks/delete/{p.pk}/"' in actual


# ---------------------------------------------------------------------------------------
#                                                                        TabHistory View
# ---------------------------------------------------------------------------------------
def test_tab_history_func():
    view = resolve('/drinks/history/')

    assert views.TabHistory == view.func.view_class


def test_tab_history_200(client_logged):
    url = reverse('drinks:tab_history')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_history_context_tab_value(client_logged):
    url = reverse('drinks:tab_history')
    response = client_logged.get(url)

    assert response.context['tab'] == 'history'


def test_tab_history_context(client_logged):
    DrinkFactory()

    url = reverse('drinks:tab_history')
    response = client_logged.get(url)

    assert 'categories' in response.context['chart']
    assert 'data_ml' in response.context['chart']
    assert 'data_alcohol' in response.context['chart']


@freeze_time('1999-1-1')
def test_tab_history_chart_consumption(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    url = reverse('drinks:tab_history')
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '<div id="chart-summary-container"></div>' in content


@freeze_time('1999-01-01')
def test_tab_history_drinks_years(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1998, 1, 1))

    url = reverse('drinks:tab_history')
    response = client_logged.get(url)

    assert response.context['chart']['categories'] == [1998, 1999]


@freeze_time('1999-01-01')
@pytest.mark.parametrize(
    'user_drink_type, drink_type, ml',
    [
        ('beer', 'beer', [2.74, 1.37]),
        ('beer', 'wine', [8.77, 4.38]),
        ('beer', 'vodka', [43.84, 21.92]),
    ]
)
def test_tab_history_drinks_data_ml(user_drink_type, drink_type, ml, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkFactory(date=date(1999, 1, 1), quantity=1, option=drink_type)
    DrinkFactory(date=date(1998, 1, 1), quantity=2, option=drink_type)

    url = reverse('drinks:tab_history')
    response = client_logged.get(url)

    assert response.context['chart']['data_ml'] == pytest.approx(ml, rel=1e-2)


@freeze_time('1999-01-01')
@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', [0.05, 0.025]),
        ('beer', 'wine', [0.16, 0.08]),
        ('beer', 'vodka', [0.8, 0.4]),
    ]
)
def test_tab_history_drinks_data_alcohol(user_drink_type, drink_type, expect, get_user, client_logged):
    get_user.drink_type = user_drink_type

    DrinkFactory(quantity=1, option=drink_type)
    DrinkFactory(date=date(1998, 1, 1), quantity=2, option=drink_type)

    url = reverse('drinks:tab_history')
    response = client_logged.get(url)

    assert response.context['chart']['data_alcohol'] == pytest.approx(expect, 0.01)


@freeze_time('1999-1-1')
def test_tab_history_categories_with_empty_year_in_between(fake_request):
    DrinkFactory(date=date(1997, 1, 1), quantity=15)
    DrinkFactory(date=date(1999, 1, 1), quantity=15)
    DrinkFactory(date=date(1999, 1, 1), quantity=15)

    class Dummy(views.TabHistory):
        pass

    view = setup_view(Dummy(), fake_request)
    actual = view.get_context_data()

    assert actual['chart']['categories'] == [1997, 1998, 1999]
    assert pytest.approx(actual['chart']['data_ml'], 0.01) == [20.55, 0.0, 41.1]
    assert pytest.approx(actual['chart']['data_alcohol'], rel=1e-1) == [0.38, 0.0, 0.75]


@freeze_time('1999-1-1')
@pytest.mark.parametrize(
    'user_drink_type, drink_type, ml, alcohol',
    [
        ('beer', 'beer', [1.37, 0.0], [0.025, 0.0]),
        ('beer', 'wine', [4.38, 0.0], [0.08, 0.0]),
        ('beer', 'vodka', [21.92, 0.0], [0.4, 0.0]),
    ]
)
def test_tab_history_categories_with_empty_current_year(user_drink_type, drink_type, ml, alcohol, get_user, fake_request):
    get_user.drink_type = user_drink_type

    DrinkFactory(date=date(1998, 1, 1), quantity=1, option=drink_type)

    class Dummy(views.TabHistory):
        pass

    view = setup_view(Dummy(), fake_request)
    actual = view.get_context_data()

    assert actual['chart']['categories'] == [1998, 1999]
    assert pytest.approx(actual['chart']['data_ml'], rel=1e-1) == ml
    assert pytest.approx(actual['chart']['data_alcohol'], rel=1e-1) == alcohol


# ---------------------------------------------------------------------------------------
#                                                                           Compare View
# ---------------------------------------------------------------------------------------
def test_compare_data_func():
    view = resolve('/drinks/compare/1/')

    assert views.Compare is view.func.view_class


def test_compare_data_200(client_logged):
    DrinkFactory()

    url = reverse('drinks:compare', kwargs={'qty': 2})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_compare_data_chart(client_logged):
    DrinkFactory()

    url = reverse('drinks:compare', kwargs={'qty': 2})
    response = client_logged.get(url)
    actual = response.context['chart']

    assert response.status_code == 200
    assert actual['serries'][0]['name'] == 1999
    assert round(actual['serries'][0]['data'][0], 2) == 16.13


# ---------------------------------------------------------------------------------------
#                                                                         CompareTwo View
# ---------------------------------------------------------------------------------------
def test_comparetwo_func():
    view = resolve('/drinks/compare/')

    assert views.CompareTwo is view.func.view_class


def test_comparetwo_200(client_logged):
    response = client_logged.get('/drinks/compare/')

    assert response.status_code == 200


def test_comparetwo_form_is_not_valid(client_logged):
    url = reverse('drinks:compare_two')
    response = client_logged.post(url, {'year1': '1999', 'year2': '2000'})
    form = response.context['form']

    assert not form.is_valid()


def test_comparetwo_form_is_valid(client_logged):
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(2000, 1, 1))

    url = reverse('drinks:compare_two')
    response = client_logged.post(url, {'year1': '1999', 'year2': '2000'})
    form = response.context['form']

    assert form.is_valid()


def test_comparetwo_chart_data(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(2020, 1, 1), quantity=10)

    url = reverse('drinks:compare_two')
    response = client_logged.post(url, {'year1': '1999', 'year2': '2020'})
    actual = response.context['chart']

    assert actual['serries'][0]['name'] == 1999
    assert round(actual['serries'][0]['data'][0], 2) == 16.13

    assert actual['serries'][1]['name'] == 2020
    assert round(actual['serries'][1]['data'][0], 2) == 161.29


# ---------------------------------------------------------------------------------------
#                                                                           Create/Update
# ---------------------------------------------------------------------------------------
def test_new_func():
    view = resolve('/drinks/index/new/')

    assert views.New is view.func.view_class


def test_update_func():
    view = resolve('/drinks/update/1/')

    assert views.Update is view.func.view_class


@pytest.mark.parametrize(
    'tab, trigger',
    [
        ('index', 'reloadIndex'),
        ('data', 'reloadData'),
        ('history', 'reloadHistory'),
        ('xxx', 'reloadData'),
    ]
)
def test_trigger_name(tab, trigger, rf):
    request = rf.get(reverse('drinks:new', kwargs={'tab': tab}))

    view = setup_view(views.New(), request)
    view.kwargs = {'tab': tab}
    actual = view.get_hx_trigger_django()

    assert actual == trigger


@freeze_time('2000-01-01')
@pytest.mark.parametrize(
    'tab, expect_url',
    [
        ('index', reverse_lazy('drinks:new', kwargs={'tab': 'index'})),
        ('data', reverse_lazy('drinks:new', kwargs={'tab': 'data'})),
        ('history', reverse_lazy('drinks:new', kwargs={'tab': 'history'})),
        ('xxx', reverse_lazy('drinks:new', kwargs={'tab': 'index'})),
    ]
)
def test_new_load_form(client_logged, tab, expect_url):
    url = reverse('drinks:new', kwargs={'tab': tab})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{expect_url}"' in actual
    assert '<input type="text" name="date" value="1999-01-01"' in actual


def test_new_tab_data(client_logged):
    data = {'date': '1999-01-01', 'quantity': 19, 'option': 'beer'}
    url = reverse('drinks:new', kwargs={'tab': 'data'})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()

    assert '19' in actual
    assert '<a role="button" hx-get="/drinks/update/1/"' in actual
    assert '<a role="button" hx-get="/drinks/update/1/"' in actual


def test_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}
    url = reverse('drinks:new', kwargs={'tab': 'data'})
    response = client_logged.post(url, data)
    form = response.context['form']

    assert not form.is_valid()


def test_update(client_logged):
    p = DrinkFactory()

    data = {'date': '1999-01-01', 'quantity': 0.68, 'option': 'beer'}
    url = reverse('drinks:update', kwargs={'pk': p.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()

    assert '0,68' in actual
    assert f'<a role="button" hx-get="/drinks/update/{p.pk}/"' in actual
    assert f'<a role="button" hx-get="/drinks/update/{p.pk}/"' in actual


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 10.0),
        ('wine', 10.0),
        ('vodka', 10.0),
        ('stdav', 10.0),
    ]
)
def test_update_load_form_convert_quantity(drink_type, expect, client_logged):
    p = DrinkFactory(quantity=10, option=drink_type)

    url = reverse('drinks:update', kwargs={'pk': p.pk})
    response = client_logged.get(url)
    form = response.context['form']

    assert f'name="quantity" value="{expect}"' in form.as_p()


def test_drinks_update_not_load_other_user(client_logged, second_user):
    DrinkFactory()
    obj = DrinkFactory(date=date(1111, 1, 1), quantity=0.666, user=second_user)

    url = reverse('drinks:update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# ---------------------------------------------------------------------------------------
#                                                                            Drink Delete
# ---------------------------------------------------------------------------------------
def test_view_drinks_delete_func():
    view = resolve('/drinks/delete/1/')

    assert views.Delete is view.func.view_class


def test_view_drinks_delete_200(client_logged):
    p = DrinkFactory()

    url = reverse('drinks:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_drinks_delete_load_form(client_logged):
    p = DrinkFactory()

    url = reverse('drinks:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url, {})
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>1999-01-01: 1.0</strong>?' in actual


def test_view_drinks_delete(client_logged):
    p = DrinkFactory()

    assert models.Drink.objects.all().count() == 1
    url = reverse('drinks:delete', kwargs={'pk': p.pk})
    client_logged.post(url)

    assert models.Drink.objects.all().count() == 0


def test_drinks_delete_other_user_get_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse('drinks:delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_drinks_delete_other_user_post_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse('drinks:delete', kwargs={'pk': obj.pk})
    client_logged.post(url)

    assert models.Drink.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                    Target Create/Update
# ---------------------------------------------------------------------------------------
def test_target_func():
    view = resolve('/drinks/index/target/new/')

    assert views.TargetNew is view.func.view_class


def test_target_update_func():
    view = resolve('/drinks/target/update/1/')

    assert views.TargetUpdate is view.func.view_class


@pytest.mark.parametrize(
    'tab, trigger',
    [
        ('index', 'reloadIndex'),
        ('data', 'reloadData'),
        ('history', 'reloadHistory'),
        ('xxx', 'reloadIndex'),
    ]
)
def test_target_get_trigger_name(tab, trigger, rf):
    request = rf.get(reverse('drinks:target_new', kwargs={'tab': tab}))

    view = setup_view(views.TargetNew(), request)
    view.kwargs = {'tab': tab}
    actual = view.get_hx_trigger_django()

    assert actual == trigger


@pytest.mark.parametrize(
    'tab, expect_url',
    [
        ('index', reverse_lazy('drinks:target_new', kwargs={'tab': 'index'})),
        ('data', reverse_lazy('drinks:target_new', kwargs={'tab': 'data'})),
        ('history', reverse_lazy('drinks:target_new', kwargs={'tab': 'history'})),
        ('xxx', reverse_lazy('drinks:target_new', kwargs={'tab': 'index'})),
    ]
)
def test_target_new_load_form(client_logged, tab, expect_url):
    url = reverse('drinks:target_new', kwargs={'tab': tab})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert response.status_code == 200
    assert f'hx-post="{expect_url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


@pytest.mark.parametrize(
    'drink_type, ml, expect',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 66, 66),
    ]
)
def test_target_new(drink_type, ml, expect, client_logged):
    data = {'year': 1999, 'quantity': ml, 'drink_type': drink_type}
    url = reverse('drinks:target_new', kwargs= {'tab': 'index'})
    client_logged.post(url, data)

    actual = models.DrinkTarget.objects.last()
    assert actual.drink_type == drink_type
    assert actual.quantity == expect


def test_target_new_invalid_data(client_logged):
    data = {'year': -2, 'quantity': 'x'}
    url = reverse('drinks:target_new', kwargs= {'tab': 'index'})
    response = client_logged.post(url, data)
    form = response.context['form']

    assert not form.is_valid()


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

    url = reverse('drinks:target_update', kwargs={'pk': p.pk})
    response = client_logged.get(url)
    form = response.context['form']

    assert f'name="quantity" value="{expect}"' in form.as_p()


@pytest.mark.parametrize(
    'drink_type, ml, expect',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 66, 66),
    ]
)
def test_target_update(drink_type, ml, expect, client_logged):
    p = DrinkTargetFactory()

    data = {'year': 1999, 'quantity': ml, 'drink_type': drink_type}
    url = reverse('drinks:target_update', kwargs={'pk': p.pk})
    client_logged.post(url, data)

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

    DrinkTargetFactory(drink_type=drink_type, quantity=ml)

    url = reverse('drinks:target_list')
    response = client_logged.get(url)
    actual = response.content.decode('utf-8')

    assert f'<td>{expect_ml}</td>' in actual
    assert f'<td>{expect_pcs}</td>' in actual


def test_target_update_not_load_other_user(client_logged, second_user):
    DrinkTargetFactory()
    obj = DrinkTargetFactory(quantity=666, user=second_user)

    url = reverse('drinks:target_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_target_empty_db(client_logged):
    response = client_logged.get('/drinks/')

    assert 'Neįvestas tikslas' in response.context["target_list"]


# ---------------------------------------------------------------------------------------
#                                                                        SelectDrink View
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
    client_logged.get(url)
    actual = User.objects.first()

    assert actual.drink_type == 'wine'


def test_select_drinks_set_default_drink_type(main_user, client_logged):
    main_user.drink_type = 'wine'
    main_user.save()

    assert User.objects.first().drink_type == 'wine'

    url = reverse('drinks:set_drink_type', kwargs={'drink_type': 'xxx'})
    client_logged.get(url)
    actual = User.objects.first()

    assert actual.drink_type == 'beer'
