import json
from datetime import date

import pytest
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import models, views


X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                             Debts Index
# ---------------------------------------------------------------------------------------
def test_debts_index_func():
    view = resolve('/debts/')

    assert views.Index == view.func.view_class


def test_debts_index_200(client_logged):
    url = reverse('debts:debts_index')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_debts_index_not_logged(client):
    url = reverse('debts:debts_index')
    response = client.get(url)

    assert response.status_code == 302
