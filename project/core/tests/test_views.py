import pytest
from django.shortcuts import reverse


@pytest.mark.django_db()
def test_set_year(login, client):
    url = reverse(
        'core:set_year',
        kwargs={'year': 1970, 'view_name': 'core:core_index'}
    )

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.profile.year == 1970


@pytest.mark.django_db()
def test_set_month(login, client):
    url = reverse(
        'core:set_month',
        kwargs={'month': 12, 'view_name': 'core:core_index'}
    )

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.wsgi_request.user.profile.month == 12
