import pytest
from django.shortcuts import reverse


def test_set_year(admin_client):
    url = reverse(
        'core:set_year',
        kwargs={'year': 1970, 'view_name': 'core:core_index'}
    )

    response = admin_client.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.profile.year == 1970


def test_set_month(admin_client):
    url = reverse(
        'core:set_month',
        kwargs={'month': 12}
    )

    response = admin_client.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.profile.month == 12
