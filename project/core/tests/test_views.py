import re
from datetime import date

import pytest
import time_machine
from django.urls import reverse

pytestmark = pytest.mark.django_db

HTMX_CONFIG = "<meta name=\"htmx-config\" content='[^']*"


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


def test_base_reads_the_htmx_config_before_htmx(client_logged):
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert content.index('<meta name="htmx-config"') < content.index("htmx.min.js")


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("bookkeeping:index", id="base"),
        pytest.param("expenses:import", id="import_page"),
    ],
)
def test_the_date_picker_translation_loads_once_on_the_page(client_logged, url):
    page = client_logged.get(reverse(url)).content.decode()
    form = client_logged.get(reverse("expenses:new")).content.decode()

    script = r"<script[^>]*src=\"[^\"]*litepicker/translations/"
    head = page.split("</head>")[0]
    assert len(re.findall(script + r"lt\.js\"", head)) == 1
    assert len(re.findall(script, page)) == 1
    assert not re.search(script, form)


@pytest.mark.parametrize(
    "pattern",
    [
        pytest.param(
            HTMX_CONFIG + re.escape('"includeIndicatorCSS": false'),
            id="no_indicator_css",
        ),
        pytest.param(
            HTMX_CONFIG + re.escape('"noSwap": [204, 304, "4xx", "5xx"]'),
            id="no_swap",
        ),
        pytest.param(
            HTMX_CONFIG + re.escape('"history": "reload"'), id="history_reload"
        ),
        pytest.param(
            re.escape('<div class="day-of-year"><span>34 / <b>365</b></span></div>'),
            id="day_of_year",
        ),
    ],
)
@time_machine.travel("1999-02-03")
def test_base_draws_on_every_page(client_logged, pattern):
    content = client_logged.get(reverse("bookkeeping:index")).content.decode()

    assert re.search(pattern, content)
