import json

import pytest
from django.http import JsonResponse
from django.urls import resolve, reverse

from .. import views

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                            Realod Index
# ---------------------------------------------------------------------------------------
def test_view_reload_index_func():
    view = resolve('/bookkeeping/reload/')

    assert views.ReloadIndex is view.func.view_class


def test_view_reload_index_render(client_logged):
    url = reverse('bookkeeping:reload_index')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


def test_view_reload_index_return_object(client_logged):
    url = reverse('bookkeeping:reload_index')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert isinstance(response, JsonResponse)


def test_view_reload_index_render_ajax_trigger(client_logged):
    url = reverse('bookkeeping:reload_index')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200

    actual = json.loads(response.content)
    assert len(actual) == 2
    assert 'no_incomes' in actual
    assert 'wealth' in actual
