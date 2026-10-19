from datetime import date

import pytest
import time_machine
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "year, expect",
    [
        pytest.param(2010, 2010, id="in_range"),
        pytest.param(1000, 1999, id="before_first_record"),
        pytest.param(3000, 1999, id="after_this_year"),
    ],
)
@time_machine.travel("2020-01-01")
def test_set_year(year, expect, main_user, client_logged):
    main_user.journal.first_record = date(1974, 1, 1)
    url = reverse("core:set_year", kwargs={"year": year})
    response = client_logged.get(url, follow=True)

    assert response.wsgi_request.user.year == expect


def test_base_leaves_the_loader_styles_to_the_stylesheet(client_logged):
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert '"includeIndicatorCSS": false' in content
    assert content.index('<meta name="htmx-config"') < content.index("htmx.min.js")


@pytest.mark.parametrize(
    "markup",
    [
        pytest.param('"noSwap": [204, 304, "4xx", "5xx"]', id="no_swap"),
        pytest.param('"history": "reload"', id="history_reload"),
        pytest.param(
            '<div class="day-of-year"><span>34 / <b>365</b></span></div>',
            id="day_of_year",
        ),
    ],
)
@time_machine.travel("1999-02-03")
def test_base_draws_on_every_page(client_logged, markup):
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert markup in content
