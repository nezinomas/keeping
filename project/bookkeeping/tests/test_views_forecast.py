import pytest
from django.urls import resolve, reverse

from .. import views

pytestmark = pytest.mark.django_db


def test_func():
    view = resolve("/bookkeeping/forecast/")

    assert views.Forecast == view.func.view_class


def test_200(client_logged):
    url = reverse("bookkeeping:forecast")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_302(client):
    url = reverse("bookkeeping:forecast")
    response = client.get(url)

    assert response.status_code == 302
