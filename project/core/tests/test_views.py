from datetime import date

import pytest
import time_machine
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "year, expect",
    [
        (2010, 2010),
        (1000, 1999),
        (3000, 1999),
    ],
)
@time_machine.travel("2020-01-01")
def test_set_year(year, expect, main_user, client_logged):
    main_user.journal.first_record = date(1974, 1, 1)
    url = reverse("core:set_year", kwargs={"year": year})
    response = client_logged.get(url, follow=True)

    assert response.wsgi_request.user.year == expect


# -------------------------------------------------------------------------------------
#                                                                          Base Template
# -------------------------------------------------------------------------------------
def test_base_leaves_the_loader_styles_to_the_stylesheet(client_logged):
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert '"includeIndicatorCSS": false' in content
    assert content.index('<meta name="htmx-config"') < content.index("htmx.min.js")


def test_base_keeps_error_responses_out_of_the_page(client_logged):
    """htmx 4 swaps 4xx/5xx by default, which would paste Django's error page
    into whatever the request targeted."""
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert '"noSwap": [204, 304, "4xx", "5xx"]' in content


def test_base_reloads_the_page_on_back(client_logged):
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert '"history": "reload"' in content
