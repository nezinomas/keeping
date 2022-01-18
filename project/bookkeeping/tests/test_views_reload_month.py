import json

import pytest
from django.http import JsonResponse
from django.urls import resolve, reverse

from .. import views

pytestmark = pytest.mark.django_db
X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}



# ---------------------------------------------------------------------------------------
#                                                                            Realod Month
# ---------------------------------------------------------------------------------------
def test_view_reload_month_func():
    view = resolve('/month/reload/')

    assert views.ReloadMonth is view.func.view_class


def test_view_reload_month_render(client_logged):
    url = reverse('bookkeeping:reload_month')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Month == response.resolver_match.func.view_class


def test_view_reload_month_render_ajax_trigger(client_logged):
    url = reverse('bookkeeping:reload_month')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200

    actual = json.loads(response.content)

    assert len(actual) == 4
    assert 'month_table' in actual
    assert 'info' in actual
    assert 'chart_expenses' in actual
    assert 'chart_targets' in actual


def test_view_reload_month_return_object(client_logged):
    url = reverse('bookkeeping:reload_month')
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert isinstance(response, JsonResponse)
