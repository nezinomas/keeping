import json
from datetime import datetime

import pandas  # need to import before freezegun, why?
import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


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
