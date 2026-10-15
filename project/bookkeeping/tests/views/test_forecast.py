import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_empty_forecast_totals_row_reads_dashes(client_logged):
    url = reverse("bookkeeping:forecast")
    content = client_logged.get(url).content.decode("utf-8")

    assert '<tfoot x-show="open">' in content
    assert content.count("<th>-</th>") == 2
    assert '<th data-sign="gain">-</th>' in content


def test_302(client):
    url = reverse("bookkeeping:forecast")
    response = client.get(url)

    assert response.status_code == 302


def test_a_user_with_no_year_raises(client_logged, main_user):
    main_user.year = None
    main_user.save()

    with pytest.raises(ValueError, match="has no year"):
        client_logged.get(reverse("bookkeeping:forecast"))
