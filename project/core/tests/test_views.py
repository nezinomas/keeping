import re
from datetime import date

import pytest
import time_machine
from django.urls import reverse

from project.counts.tests.factories import CountTypeFactory

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


@pytest.mark.parametrize(
    "url, panel_class",
    [
        pytest.param("expenses:index", "grid-one-col", id="grid"),
        pytest.param("drinks:index", "", id="no_grid"),
    ],
)
def test_a_paper_page_draws_its_tab_panel(client_logged, url, panel_class):
    content = client_logged.get(reverse(url)).content.decode()

    assert content.count("<main") == 1
    assert (
        f'<main id="tab_content" class="{panel_class}" role="tabpanel"'
        " :aria-labelledby=\"'tab-' + tab\">"
    ) in content


@pytest.mark.parametrize(
    "url, args",
    [
        pytest.param("expenses:index", [], id="expenses"),
        pytest.param("incomes:index", [], id="incomes"),
        pytest.param("books:index", [], id="books"),
        pytest.param("plans:index", [], id="plans"),
        pytest.param("counts:index", ["count-type"], id="counts"),
        pytest.param("drinks:index", [], id="drinks"),
    ],
)
def test_every_script_a_paper_page_runs_carries_the_csp_nonce(client_logged, url, args):
    CountTypeFactory()
    content = client_logged.get(reverse(url, args=args)).content.decode()

    # a chart's json_script is data, which CSP never runs
    scripts = [
        tag
        for tag in re.findall(r"<script\b[^>]*>", content)
        if 'type="application/json"' not in tag
    ]
    assert scripts
    assert [tag for tag in scripts if "nonce=" not in tag] == []
