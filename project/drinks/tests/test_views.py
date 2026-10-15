import json
import re
from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext as _

from ...core.mixins import kwargs as core_kwargs
from ...core.tests.utils import setup_view
from ...users.tests.factories import User
from .. import models, views
from .factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db

TABS = {
    "index": "drinks:tab_index",
    "trends": "drinks:tab_trends",
    "habits": "drinks:tab_habits",
    "risk": "drinks:tab_risk",
    "history": "drinks:tab_history",
    "data": "drinks:tab_data",
}


def chart_data(content: str, chart: str) -> dict:
    """The JSON a chart script carries; a chart the page lacks fails here."""
    match = re.search(
        rf'<script id="chart-{chart}-data" type="application/json">(.*?)</script>',
        content,
        re.S,
    )

    assert match, f"no data script rendered for the {chart} chart"
    return json.loads(match.group(1))


# IndexView
def test_index_heads_the_page_where_only_a_reader_hears_it(client_logged):
    content = client_logged.get(reverse("drinks:index")).content.decode("utf-8")

    assert content.count("<h1") == 1
    assert f'<h1 class="visually-hidden">{_("Drinks")}</h1>' in content


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="page"),
        # the fragment carries the title so htmx can swap it
        pytest.param({"HTTP_HX_REQUEST": "true"}, id="fragment"),
    ],
)
@pytest.mark.parametrize(
    "tab, expected",
    [("index", "Overview"), ("trends", "Trends"), ("data", "Data")],
)
def test_tab_names_itself_in_the_browser_title(client_logged, headers, tab, expected):
    response = client_logged.get(reverse(TABS[tab]), **headers)

    assert f"<title>{_('Drinks')} | {_(expected)}</title>" in response.content.decode()


def test_index_takes_its_legend_position_from_the_paper_charts(client_logged):
    # chart_paper.js places every paper legend, so Drinks keeps no file of its own
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert "js/chart_paper.js" in content
    assert "js/chart_drinks_legend.js" not in content


def test_index_wraps_every_tab_in_the_paper_skin(client_logged):
    # the wrapper scopes the tokens every Drinks chart reads, so no other app's
    # page inherits them
    response = client_logged.get(reverse("drinks:index"))

    assert 'class="paper-skin"' in response.content.decode()


def test_index_quick_add(client_logged):
    # a drink is added from the bottom-pill widget, not from the nav
    url = reverse("drinks:index")
    response = client_logged.get(url)
    content = response.content.decode()

    assert f'hx-post="{reverse("drinks:quick_add")}"' in content
    assert 'name="quantity"' in content
    assert 'class="quick-add__pill"' in content
    assert '<button type="submit" class="button-secondary">' in content
    assert (
        "htmx.ajax('GET', '/drinks/' + document.getElementById('quick-add-tab').value + '/new/', '#mainModal')"
        in content
    )
    assert 'class="select-wrapper quick-add__type"' in content
    assert '<select name="option" class="form-select"' in content


def test_index_has_no_inline_separator_script(client_logged):
    response = client_logged.get(reverse("drinks:index"))

    assert "input.value.replace(/,/g, '.')" not in response.content.decode()


def test_index_switcher_is_not_swapped_out_of_band(client_logged):
    """The page draws the control itself; only a tab reload replaces it."""
    response = client_logged.get(reverse("drinks:index"))

    assert "hx-swap-oob" not in response.content.decode()


def test_index_quick_add_prefilled_and_esc_close(client_logged, main_user):
    main_user.drink_type = "wine"
    main_user.save()

    url = reverse("drinks:index")
    response = client_logged.get(url)
    content = response.content.decode()

    assert '@keydown.window.escape="open = false"' in content
    assert 'x-model="quantity"' in content
    assert 'x-model="option"' in content
    assert "beer: '1'" in content
    assert "wine: '150'" in content
    assert "vodka: '40'" in content
    assert "stdav: '1'" in content
    assert "event.detail.ctx.response.raw.ok" in content
    assert "Alpine.$data(this).open = false" in content


def test_index_links(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)
    content = response.content.decode()

    pattern = re.compile(
        r'<button\s+id="tab-\w+".*?hx-get="(.*?)".*?>\s*(\w+)\s*</button>', re.S
    )
    res = re.findall(pattern, content)

    assert len(res) == 6
    assert res[0][0] == reverse("drinks:tab_index")
    assert res[0][1] == "Apžvalga"

    assert res[1][0] == reverse("drinks:tab_trends")
    assert res[1][1] == "Tendencijos"

    assert res[2][0] == reverse("drinks:tab_habits")
    assert res[2][1] == "Įpročiai"

    assert res[3][0] == reverse("drinks:tab_risk")
    assert res[3][1] == "Rizikos"

    assert res[4][0] == reverse("drinks:tab_history")
    assert res[4][1] == "Istorija"

    assert res[5][0] == reverse("drinks:tab_data")
    assert res[5][1] == "Duomenys"


def test_index_renders_the_tab_nav_once(client_logged):
    # the nav sits outside #tab_content, so a tab swap cannot replace it
    response = client_logged.get(reverse("drinks:index"))

    assert response.content.decode().count('class="subnav"') == 1


def test_index_nav_tracks_the_open_tab_in_alpine(client_logged):
    # rendered once on Overview, so the mark moves client-side from there
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert "x-data=\"{ tab: 'index' }\"" in content
    assert "@click=\"tab = 'habits'\"" in content
    assert ":class=\"{ active: tab === 'habits' }\"" in content
    assert 'class="tab active"' in content
    assert content.count('class="tab active"') == 1


def test_index_drink_type_links_carry_the_open_tab(client_logged):
    # not baked into the url: htmx reads it off the input at click time
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert '<input type="hidden" id="current-tab" name="tab" :value="tab">' in content
    assert 'hx-include="#current-tab"' in content

    for drink_type in models.DrinkType.values:
        url = reverse("drinks:set_drink_type", kwargs={"drink_type": drink_type})
        assert f'hx-get="{url}" hx-include="#current-tab"' in content
        assert f"{url}?tab=" not in content


def test_index_switcher_sits_in_the_quick_add_bar(client_logged):
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert '<div class="quick-add__bar">' in content
    assert content.count('id="drink-type-control"') == 1
    # the nav lost it: the bar is the only place a drink type is chosen
    nav = content.split('<nav class="subnav"')[1].split("</nav>")[0]
    assert "dropdown" not in nav


def test_index_quick_add_preselects_the_users_drink_type(client_logged, main_user):
    main_user.drink_type = "wine"
    main_user.save()

    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert "option: 'wine'" in content
    assert '<option value="wine" selected>' in content
    assert '<option value="beer" selected>' not in content


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", "Alus"),
        ("wine", "Vynas"),
        ("vodka", "Degtinė"),
        ("stdav", "Std Av"),
    ],
)
def test_index_select_drink_drop_down_title(
    drink_type, expect, main_user, client_logged
):
    main_user.drink_type = drink_type
    main_user.save()

    url = reverse("drinks:index")
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert f'<button class="dropdown__btn">{expect}</button>' in content


def test_index_drink_type_press_closes_the_menu(client_logged):
    # :focus-within holds the menu open, so the press has to drop the focus
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert content.count('@click="$el.blur()"') == len(models.DrinkType.values)


@pytest.mark.parametrize(
    "url_name, expect",
    [
        ("drinks:tab_index", "Vynas"),
        ("drinks:tab_trends", "Vynas"),
        ("drinks:tab_history", "Vynas"),
        ("drinks:tab_habits", "Std Av"),
        ("drinks:tab_risk", "Std Av"),
    ],
)
def test_tab_reload_swaps_the_switcher_out_of_band(
    url_name, expect, main_user, client_logged
):
    """A tab arrives with the control its own readings are in."""
    main_user.drink_type = "wine"
    main_user.save()

    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<div id="drink-type-control" hx-swap-oob="true">' in content
    assert expect in content


@pytest.mark.parametrize("url_name", ["drinks:tab_habits", "drinks:tab_risk"])
def test_tab_reading_std_av_names_the_unit_and_offers_no_choice(
    url_name, client_logged
):
    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<span class="drink-type-unit">[ Std Av ]</span>' in content
    assert "dropdown" not in content


@pytest.mark.parametrize("url_name", ["drinks:tab_habits", "drinks:tab_risk"])
def test_tab_reading_std_av_says_the_whole_tab_is_in_it(url_name, client_logged):
    """The caption is part of the one control, not a label sitting next to it."""
    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert (
        '<span class="drink-type-fixed">'
        '<span class="drink-type-note">Duomenys rodomi</span>'
        '<span class="drink-type-unit">[ Std Av ]</span>'
        "</span>"
    ) in content


@pytest.mark.parametrize(
    "url_name", ["drinks:tab_index", "drinks:tab_trends", "drinks:tab_history"]
)
def test_tab_choosing_the_unit_carries_no_caption(url_name, client_logged):
    """The switcher says what it is by being pressable."""
    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")

    assert _("Data shown as") not in response.content.decode()


def test_tab_reading_no_amount_empties_the_control(client_logged):
    response = client_logged.get(reverse("drinks:tab_data"), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<div id="drink-type-control" hx-swap-oob="true"></div>' in content


# Tab urls
def tab_button(content: str, name: str) -> str:
    """The attributes of one tab button, so a test does not pin their order."""
    match = re.search(rf'<button\s+id="tab-{name}"(.*?)>', content, re.S)

    assert match, f"no button rendered for the {name} tab"
    return match.group(1)


@pytest.mark.parametrize("url_name", list(TABS.values()))
def test_tab_url_opens_the_whole_page(url_name, client_logged):
    """A pushed url has to answer a bookmark and a reload, not just a swap."""
    response = client_logged.get(reverse(url_name))
    content = response.content.decode()

    assert 'role="tablist"' in content
    assert 'id="quick-add"' in content


@pytest.mark.parametrize("tab, url_name", list(TABS.items()))
def test_tab_url_opens_on_its_own_tab(tab, url_name, client_logged):
    response = client_logged.get(reverse(url_name))
    content = response.content.decode()

    assert f"{{ tab: '{tab}' }}" in content
    assert 'aria-selected="true"' in tab_button(content, tab)


@pytest.mark.parametrize("url_name", list(TABS.values()))
def test_tab_url_over_htmx_is_only_the_fragment(url_name, client_logged):
    # the page a fragment lands in owns the nav
    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert 'role="tablist"' not in content
    assert 'class="subnav"' not in content


def test_tab_url_restoring_history_is_the_whole_page(client_logged):
    """Back asks over htmx too, and swaps what comes back into the whole body."""
    response = client_logged.get(
        reverse("drinks:tab_risk"),
        HTTP_HX_REQUEST="true",
        HTTP_HX_HISTORY_RESTORE_REQUEST="true",
    )

    assert 'role="tablist"' in response.content.decode()


@pytest.mark.parametrize("tab", list(TABS))
def test_tab_button_pushes_its_url(tab, client_logged):
    attrs = tab_button(client_logged.get(reverse("drinks:index")).content.decode(), tab)

    assert f'hx-get="{reverse(TABS[tab])}"' in attrs
    assert 'hx-push-url="true"' in attrs


@pytest.mark.parametrize("tab", list(TABS))
def test_tab_button_shows_the_loader_while_it_fetches(tab, client_logged):
    attrs = tab_button(client_logged.get(reverse("drinks:index")).content.decode(), tab)

    assert 'hx-indicator="#indicator"' in attrs


@pytest.mark.parametrize("tab", list(TABS))
def test_every_tab_button_is_a_tab(tab, client_logged):
    attrs = tab_button(client_logged.get(reverse("drinks:index")).content.decode(), tab)

    assert 'role="tab"' in attrs
    assert 'aria-controls="tab_content"' in attrs


@pytest.mark.parametrize(
    "open_attr, closed_attr",
    [
        pytest.param(
            'aria-selected="true"',
            'aria-selected="false"',
            id="only_the_open_tab_is_selected",
        ),
        # arrow keys move between tabs, so Tab enters the row once and leaves it
        pytest.param(
            'tabindex="0"',
            'tabindex="-1"',
            id="the_open_tab_is_the_only_one_in_the_focus_order",
        ),
    ],
)
def test_the_open_tab_alone_is_marked_open(client_logged, open_attr, closed_attr):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert open_attr in tab_button(content, "index")
    assert all(closed_attr in tab_button(content, t) for t in list(TABS)[1:])


@pytest.mark.parametrize(
    "tab, titles",
    [
        pytest.param("index", ["Consumption by month", "Calendar"], id="index"),
        pytest.param("habits", ["Weekday profile", "Typical year"], id="habits"),
        pytest.param(
            "trends", ["Rolling average", "Cumulative (year over year)"], id="trends"
        ),
        pytest.param(
            "risk", ["Weekly units with risk bands", "Heavy days per month"], id="risk"
        ),
    ],
)
def test_tab_titles_its_panels(client_logged, tab, titles):
    content = client_logged.get(reverse(TABS[tab])).content.decode()

    for title in titles:
        assert f'<h2 class="panel__title">{_(title)}</h2>' in content


@pytest.mark.parametrize(
    "tab, charts, markup, cards",
    [
        pytest.param(
            "index",
            ["quantity", "consumption"],
            # the Converted table's rows exist only while the breakdown has data
            ('<tr class="main__total">', "<td>0,40</td>"),
            6,
            id="index",
        ),
        pytest.param("habits", ["weekday"], (), 1, id="habits"),
        pytest.param("trends", ["trend"], (), 5, id="trends"),
        pytest.param("risk", ["weekly", "heavy"], (), 4, id="risk"),
    ],
)
def test_tab_renders_its_charts_and_cards(client_logged, tab, charts, markup, cards):
    DrinkFactory()

    page = client_logged.get(reverse(TABS[tab])).content.decode()

    for chart in charts:
        assert isinstance(chart_data(page, chart), dict)
    for text in markup:
        assert text in page
    assert page.count('<div class="trend-card">') == cards


def test_back_reloads_the_page_rather_than_restoring_a_snapshot(client_logged):
    """htmx 4 has no ajax history restore, so Back is a plain page load."""
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert 'hx-history="false"' not in content
    assert "refreshOnHistoryMiss" not in content


def test_the_tabs_carry_a_tablist(client_logged):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert 'role="tablist"' in content
    assert 'role="tabpanel"' in content


# TabIndex View
def test_tab_index_titles_the_converted_panel(client_logged):
    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    assert f'<h2 class="panel__title">{_("Converted")}, {_("pcs")}</h2>' in content
    assert (
        '<p class="panel__subtitle">'
        f"{_('The same amount of alcohol, converted to different drink types.')}"
        "</p>" in content
    )


@pytest.mark.parametrize(
    "markup",
    [
        pytest.param(
            '<section class="panel panel--table" id="breakdown">',
            id="breakdown_is_a_table_panel",
        ),
        # the Panel title carries the caption's text, so a sighted user reads it
        # once; the table still names itself for a screen reader
        pytest.param(
            '<caption class="visually-hidden">',
            id="breakdown_caption_is_visually_hidden",
        ),
    ],
)
def test_tab_index_breakdown_markup(client_logged, markup):
    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    assert markup in content


@pytest.mark.parametrize("panel_id", ["panel-overview", "panel-calendar"])
def test_tab_index_figure_panels_keep_their_frame(client_logged, panel_id):
    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    assert f'<section class="panel" id="{panel_id}">' in content


def _tab_queries(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def test_tab_index_query_count_does_not_grow_with_the_drinks(client_logged):
    url = reverse("drinks:tab_index")

    for i in range(2):
        DrinkFactory(date=date(1999, 1, i + 1))
    two = _tab_queries(client_logged, url)

    for i in range(2, 6):
        DrinkFactory(date=date(1999, 1, i + 1))
    six = _tab_queries(client_logged, url)

    assert six == two


def test_tab_index_daily_limit_edit_link_uses_target_update(client_logged):
    target = DrinkTargetFactory()

    url = reverse("drinks:tab_index")
    response = client_logged.get(url)
    content = response.content.decode()

    # with a saved target the pencil points at target_update
    edit_url = reverse("drinks:target_update", kwargs={"pk": target.pk})
    assert (
        f'<button type="button" class="trend-card__edit" hx-get="{edit_url}"' in content
    )


def test_tab_index_daily_limit_edit_link_sits_above_the_unit(client_logged):
    DrinkTargetFactory()

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    meta = re.search(r'<span class="trend-card__meta">(.*?)</div>', content, re.S)
    assert meta
    assert meta.group(1).index("trend-card__edit") < meta.group(1).index(
        "trend-card__unit"
    )


def test_tab_index_info_icon_sits_above_the_unit(client_logged):
    DrinkFactory()

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    metas = re.findall(r'<span class="trend-card__meta">(.*?)</div>', content, re.S)
    stacked = [
        m
        for m in metas
        if "trend-card__info" in m
        and "trend-card__unit" in m
        and m.index("trend-card__info") < m.index("trend-card__unit")
    ]
    assert stacked


@time_machine.travel("1999-06-01")
def test_tab_index_renders_the_direction_arrow_in_its_own_element(client_logged):
    """The arrow is set below the figure's size, so it needs its own element."""
    # Drinking days has a direction only with a year to compare against
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=8)

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    assert 'class="trend-card__arrow"' in content


@time_machine.travel("1999-06-01")
def test_tab_index_renders_the_state_modifier_for_a_compared_card(client_logged):
    """The state is resolved from the direction, so the template reaches a property."""
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=8)

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    assert 'class="trend-card__value trend-card__value--improving"' in content
    assert 'trend-card__value--"' not in content


def test_tab_index_renders_the_unit_apart_from_the_figure(client_logged):
    """The skin sets a unit at a third of the figure's size, so it needs an element."""
    DrinkFactory()

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    assert '<span class="trend-card__unit">L</span>' in content


def test_tab_index_omits_the_unit_element_when_there_is_no_unit(client_logged):
    DrinkFactory()

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    assert '<span class="trend-card__unit"></span>' not in content


def test_tab_index_calendar_days_are_reachable_by_keyboard(client_logged):
    DrinkFactory(date=date(1999, 1, 5), stdav=2.5, option="beer")

    response = client_logged.get(reverse("drinks:tab_index"))
    html = response.content.decode("utf-8")

    assert 'tabindex="-1" aria-label="1999-01-05, ' in html


def test_tab_index_htmx_fragment_carries_no_inline_script(client_logged):
    DrinkFactory(date=date(1999, 1, 5), stdav=2.5, option="beer")

    response = client_logged.get(reverse("drinks:tab_index"), HTTP_HX_REQUEST="true")
    fragment = response.content.decode("utf-8")

    opening_tags = re.findall(r"<script[^>]*>", fragment)

    assert "heat-card" in fragment
    assert opening_tags
    assert all('type="application/json"' in tag for tag in opening_tags)


def test_tab_index_loads_the_calendar_script_as_a_static_file(client_logged):
    DrinkFactory(date=date(1999, 1, 5), stdav=2.5, option="beer")

    response = client_logged.get(reverse("drinks:tab_index"))
    html = response.content.decode("utf-8")

    assert "js/calendar.js" in html


# TypicalYearChart View
def test_tab_habits_loads_the_typical_year_chart(client_logged):
    # the container fetches itself, so the pooled range never depends on the tab
    response = client_logged.get(reverse("drinks:tab_habits"))
    content = response.content.decode()

    assert 'id="chart-typical-year-container"' in content
    assert f'hx-get="{reverse("drinks:typical_year")}"' in content
    assert 'id="typical-year-form"' in content


def test_tab_habits_renders_the_pooled_range_presets(client_logged):
    response = client_logged.get(reverse("drinks:tab_habits"))
    content = response.content.decode()

    assert f'hx-get="{reverse("drinks:typical_year_all")}"' in content
    for qty in (2, 3, 5):
        url = reverse("drinks:typical_year_last", kwargs={"qty": qty})
        assert f'hx-get="{url}"' in content

    assert _("All years") in content
    assert _("5 years") in content


def test_tab_habits_offers_no_preset_for_the_header_year(client_logged):
    # the header year is drawn in front already, so pooling it on its own would
    # plot the same twelve months twice
    content = client_logged.get(
        reverse("drinks:tab_habits"), HTTP_HX_REQUEST="true"
    ).content.decode()

    url = reverse("drinks:typical_year_last", kwargs={"qty": 1})

    assert f'hx-get="{url}"' not in content
    assert ">1999<" not in content


def test_tab_habits_clears_the_pooled_layer_back_to_the_header_year(client_logged):
    content = client_logged.get(reverse("drinks:tab_habits")).content.decode()

    # the bare url is the state the tab opens on: the header year, nothing behind
    url = reverse("drinks:typical_year")
    clear = f'hx-get="{url}" hx-target="#chart-typical-year-container">{_("Clear")}<'

    assert clear in content
    # it undoes a Filter, so it sits after the form rather than among the presets
    assert content.index('id="typical-year-form"') < content.index(clear)


def test_typical_year_opens_on_the_header_year_alone(client_logged):
    # the pooled range is a reading to ask for: it loads on a preset or on
    # Filter, never on the first fetch
    DrinkFactory(date=date(1995, 1, 1))
    DrinkFactory(date=date(1999, 1, 1))

    page = client_logged.get(reverse("drinks:typical_year")).content.decode()
    layers = chart_data(page, "typical-year")["layers"]

    assert [layer["label"] for layer in layers] == ["1999"]


def test_typical_year_preset_fills_the_form_with_the_pooled_span(client_logged):
    # a year before the span, so the form's own default (the first year) differs
    DrinkFactory(date=date(1997, 1, 1))
    DrinkFactory(date=date(1998, 1, 1))
    DrinkFactory(date=date(1999, 1, 1))

    url = reverse("drinks:typical_year_last", kwargs={"qty": 2})
    content = client_logged.get(url).content.decode()

    assert 'name="year_from" value="1998"' in content
    assert 'name="year_to" value="1999"' in content


def test_typical_year_valid_post_pools_the_asked_range(client_logged):
    DrinkFactory(date=date(1998, 1, 1))
    DrinkFactory(date=date(1999, 1, 1))

    url = reverse("drinks:typical_year")
    response = client_logged.post(url, {"year_from": "1998", "year_to": "1999"})
    layers = chart_data(response.content.decode(), "typical-year")["layers"]

    assert "1998–1999" in layers[0]["label"]
    assert layers[1]["label"] == "1999"
    assert "HX-Retarget" not in response


@time_machine.travel("1999-06-01")
def test_every_figure_stops_at_the_views_today(client_logged, mocker):
    mocker.patch.object(
        core_kwargs, "date", mocker.Mock(today=lambda: date(1999, 3, 1))
    )
    DrinkFactory(date=date(1998, 1, 1), stdav=2.5)
    DrinkFactory(date=date(1999, 1, 15), stdav=2.5)
    DrinkFactory(date=date(1999, 3, 1), stdav=2.5)
    DrinkFactory(date=date(1999, 4, 10), stdav=2.5)

    dry = client_logged.get(reverse("drinks:tab_index")).context["cards"][0]
    typical = client_logged.get(reverse("drinks:typical_year")).content.decode()
    compare = client_logged.get(reverse("drinks:compare", kwargs={"qty": 1}))
    months = chart_data(compare.content.decode(), "history")["series"][0]["data"]
    history = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert (dry.value, dry.note) == ("0", "1999-03-01")
    assert len(chart_data(typical, "typical-year")["layers"][0]["intensity"]) == 3
    assert len(months) == 3
    # 7.5 Std Av of beer over Jan 1 to Mar 1, the 60 days the view has reached
    assert chart_data(history, "summary")["data_ml"][-1] == 25.0


def test_tab_risk_heavy_panel_leaves_the_threshold_to_its_chart(client_logged):
    content = client_logged.get(reverse("drinks:tab_risk")).content.decode()

    assert "panel__subtitle" not in content


@time_machine.travel("1999-06-01")
def test_tab_index_renders_each_explanation_part_as_its_own_paragraph(client_logged):
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=7)

    url = reverse("drinks:tab_index")
    response = client_logged.get(url, HTTP_HX_REQUEST="true")
    content = response.content.decode()

    card = next(c for c in response.context["cards"] if c.title == _("Drinking days"))
    assert len(card.explanation) == 3
    for part in card.explanation:
        assert f"<p>{escape(part)}</p>" in content
    # a label cannot hold markup, so it stays the parts run together
    assert f'aria-label="{escape(" ".join(card.explanation))}"' in content


# TabData View
def test_tab_data_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse("drinks:tab_data")
    response = client_logged.get(url)

    assert "<b>1999</b> metais įrašų nėra." in response.content.decode("utf-8")


def test_tab_data(client_logged):
    p = DrinkFactory(stdav=47.5)
    response = client_logged.get(reverse("drinks:tab_data"))

    actual = response.content.decode("utf-8")

    assert "19,0" in actual
    assert f'<a role="button" hx-get="{reverse("drinks:update", args=[p.pk])}"' in (
        actual
    )
    assert f'<a role="button" hx-get="{reverse("drinks:delete", args=[p.pk])}"' in (
        actual
    )


def test_tab_data_date_column_header(client_logged):
    DrinkFactory()
    response = client_logged.get(reverse("drinks:tab_data"))

    actual = response.content.decode("utf-8")

    assert '<th class="text-left">Data</th>' in actual
    assert '<th class="text-left">Duomenys</th>' not in actual
    assert '<th class="text-left">Gėrimo tipas</th>' in actual


def test_tab_data_quantity_value(client_logged):
    # the unit/rounding rules live in DrinkQuantity.display and are asserted in
    # tests/lib/test_drink_quantity.py; this only pins the template to it
    DrinkFactory(stdav=2.5, option="beer", converted_from_ml=True)
    response = client_logged.get(reverse("drinks:tab_data"))

    actual = response.content.decode("utf-8")

    assert "500 ml" in actual


# TabHistory View
def test_tab_history_renders_the_summary_chart_data(client_logged):
    DrinkFactory()

    page = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert {"categories", "data_ml", "data_alcohol"} <= set(chart_data(page, "summary"))


def test_tab_history_titles_its_panels(client_logged):
    DrinkFactory()
    content = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert f'<h2 class="panel__title">{_("Drinks")}</h2>' in content
    assert f'<h2 class="panel__title">{_("Year comparison")}</h2>' in content


@time_machine.travel("1999-1-1")
def test_tab_history_has_unified_compare_panel(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    url = reverse("drinks:tab_history")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert 'id="historical-data"' in content
    assert 'id="chart-history-container"' in content

    assert f'hx-get="{reverse("drinks:compare", kwargs={"qty": 2})}"' in content
    assert f'hx-get="{reverse("drinks:compare", kwargs={"qty": 3})}"' in content
    assert f'hx-get="{reverse("drinks:compare", kwargs={"qty": 7})}"' in content
    assert "Visi metai" not in content
    assert "All years" not in content

    assert 'id="compare-form"' in content
    assert 'name="year1"' in content
    assert 'name="year2"' in content
    assert f'hx-post="{reverse("drinks:compare_two")}"' in content
    assert 'hx-target="#chart-history-container"' in content

    assert 'id="compare-form-and-chart"' not in content
    assert "chart-compare-two" not in content


@time_machine.travel("1999-1-1")
def test_tab_history_chart_auto_loads_default_comparison(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    url = reverse("drinks:tab_history")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert 'hx-trigger="load"' in content


def test_tab_history_hides_compare_panel_without_records(client_logged):
    url = reverse("drinks:tab_history")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert 'id="historical-data"' not in content
    assert 'id="chart-history-container"' not in content
    assert 'id="compare-form"' not in content


# Compare View
def test_compare_data_chart(client_logged):
    DrinkFactory(stdav=2.5)

    url = reverse("drinks:compare", kwargs={"qty": 2})
    response = client_logged.get(url)
    first = chart_data(response.content.decode(), "history")["series"][0]

    assert first["name"] == 1999
    assert round(first["data"][0], 2) == 16.13


# CompareTwo View
def test_comparetwo_get_renders_the_year_pair_form(client_logged):
    response = client_logged.get(reverse("drinks:compare_two"))
    content = response.content.decode()

    assert f'hx-post="{reverse("drinks:compare_two")}"' in content
    assert 'name="year1"' in content
    assert 'name="year2"' in content


def test_compare_data_includes_form_and_oob_swap(client_logged):
    DrinkFactory()

    url = reverse("drinks:compare", kwargs={"qty": 2})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert 'id="compare-form"' in content
    assert 'hx-swap-oob="true"' in content


def test_comparetwo_valid_post_renders_the_pair(client_logged):
    DrinkFactory(date=date(1998, 1, 1))
    DrinkFactory(date=date(1999, 1, 1))

    url = reverse("drinks:compare_two")
    response = client_logged.post(url, {"year1": "1998", "year2": "1999"})
    series = chart_data(response.content.decode(), "history")["series"]

    assert [serie["name"] for serie in series] == [1998, 1999]
    assert "HX-Retarget" not in response


@pytest.mark.parametrize(
    "url_name, data, form, chart",
    [
        pytest.param(
            "drinks:compare_two",
            {"year1": "1999", "year2": "2000"},
            "#compare-form",
            "chart-history-data",
            id="compare_two",
        ),
        pytest.param(
            "drinks:typical_year",
            {"year_from": "2005", "year_to": "1999"},
            "#typical-year-form",
            "chart-typical-year-data",
            id="typical_year",
        ),
    ],
)
def test_invalid_form_retargets_itself_and_leaves_the_chart(
    client_logged, url_name, data, form, chart
):
    response = client_logged.post(reverse(url_name), data)
    content = response.content.decode()

    assert response["HX-Retarget"] == form
    assert response["HX-Reswap"] == "outerHTML"
    assert 'aria-invalid="true"' in content
    assert chart not in content


# Create/Update
@pytest.mark.parametrize(
    "view, url_name, tab, trigger",
    [
        pytest.param(views.New, "drinks:new", "index", "reloadIndex", id="new_index"),
        pytest.param(views.New, "drinks:new", "data", "reloadData", id="new_data"),
        pytest.param(
            views.New, "drinks:new", "history", "reloadHistory", id="new_history"
        ),
        pytest.param(views.New, "drinks:new", "xxx", "reloadData", id="new_unknown"),
        pytest.param(
            views.TargetNew,
            "drinks:target_new",
            "index",
            "reloadIndex",
            id="target_index",
        ),
        pytest.param(
            views.TargetNew, "drinks:target_new", "data", "reloadData", id="target_data"
        ),
        pytest.param(
            views.TargetNew,
            "drinks:target_new",
            "history",
            "reloadHistory",
            id="target_history",
        ),
        pytest.param(
            views.TargetNew,
            "drinks:target_new",
            "xxx",
            "reloadIndex",
            id="target_unknown",
        ),
    ],
)
def test_trigger_name(view, url_name, tab, trigger, rf):
    request = rf.get(reverse(url_name, kwargs={"tab": tab}))

    instance = setup_view(view(), request)
    instance.kwargs = {"tab": tab}
    actual = instance.get_hx_trigger_django()

    assert actual == trigger


@pytest.mark.parametrize(
    "url_name, field",
    [
        pytest.param(
            "drinks:new",
            '<input type="text" name="date" value="1999-01-01"',
            id="new",
        ),
        pytest.param(
            "drinks:target_new",
            '<input type="text" name="year" value="1999"',
            id="target_new",
        ),
    ],
)
@pytest.mark.parametrize(
    "tab, posts_to",
    [
        ("index", "index"),
        ("data", "data"),
        ("history", "history"),
        ("xxx", "index"),
    ],
)
@time_machine.travel("2000-1-1")
def test_new_load_form(client_logged, url_name, field, tab, posts_to):
    url = reverse(url_name, kwargs={"tab": tab})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{reverse(url_name, kwargs={"tab": posts_to})}"' in actual
    assert field in actual


def test_new_tab_data(client_logged):
    data = {"date": "1999-01-01", "stdav": 19, "option": "beer"}
    url = reverse("drinks:new", kwargs={"tab": "data"})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()
    drink = models.Drink.objects.get()

    assert "19" in actual
    assert f'<a role="button" hx-get="{reverse("drinks:update", args=[drink.pk])}"' in (
        actual
    )


@pytest.mark.parametrize(
    "url_name, tab, data, model",
    [
        pytest.param(
            "drinks:new",
            "data",
            {"date": -2, "stdav": "x"},
            models.Drink,
            id="new",
        ),
        pytest.param(
            "drinks:target_new",
            "index",
            {"year": -2, "quantity": "x"},
            models.DrinkTarget,
            id="target_new",
        ),
    ],
)
def test_new_form_rejects_invalid_data(client_logged, url_name, tab, data, model):
    url = reverse(url_name, kwargs={"tab": tab})
    response = client_logged.post(url, data)

    assert 'aria-invalid="true"' in response.content.decode()
    assert not model.objects.exists()


def test_update(client_logged):
    p = DrinkFactory()

    data = {"date": "1999-01-01", "stdav": 0.68, "option": "beer"}
    url = reverse("drinks:update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()

    assert url in actual
    assert "0,7 vnt" in actual
    assert f'<a role="button" hx-get="{url}"' in actual


@pytest.mark.parametrize(
    "converted, expect",
    [
        (False, 1.0),
        (True, 500.0),
    ],
)
def test_update_load_form_prefills_typed_quantity(converted, expect, client_logged):
    # which number the user gets back is DrinkQuantity.value, asserted in
    # tests/lib/test_drink_quantity.py; this only pins the form to it
    p = DrinkFactory(stdav=2.5, option="beer", converted_from_ml=converted)

    url = reverse("drinks:update", kwargs={"pk": p.pk})
    content = client_logged.get(url).content.decode()

    assert f'name="stdav" value="{expect}"' in content


def test_drinks_update_not_load_other_user(client_logged, second_user):
    DrinkFactory()
    obj = DrinkFactory(date=date(1111, 1, 1), stdav=0.666, user=second_user)

    url = reverse("drinks:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# Drink Delete
def test_view_drinks_delete_load_form(client_logged):
    p = DrinkFactory()

    url = reverse("drinks:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url, {})
    actual = response.content.decode()

    assert url in actual
    assert f'hx-post="{url}"' in actual
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01, beer, 200ml</strong>?" in actual
    )


def test_view_drinks_delete(client_logged):
    p = DrinkFactory()

    assert models.Drink.objects.all().count() == 1
    url = reverse("drinks:delete", kwargs={"pk": p.pk})
    client_logged.post(url)

    assert models.Drink.objects.all().count() == 0


def test_drinks_delete_other_user_get_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse("drinks:delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_drinks_delete_other_user_post_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse("drinks:delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert models.Drink.objects.all().count() == 1


# Target Create/Update
@pytest.mark.parametrize(
    "drink_type, ml, expect",
    [
        ("beer", 500, 2.5),
        ("wine", 750, 8),
        ("vodka", 1000, 40),
        ("stdav", 66, 66),
    ],
)
def test_target_new(drink_type, ml, expect, client_logged):
    data = {"year": 1999, "quantity": ml, "drink_type": drink_type}
    url = reverse("drinks:target_new", kwargs={"tab": "index"})
    client_logged.post(url, data)

    actual = models.DrinkTarget.objects.last()
    assert actual.drink_type == drink_type
    assert actual.quantity == expect


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", 500.0),
        ("wine", 750.0),
        ("vodka", 1000.0),
        ("stdav", 1.0),
    ],
)
def test_target_update_load_form_convert_quantity(drink_type, expect, client_logged):
    p = DrinkTargetFactory(quantity=expect, drink_type=drink_type)

    url = reverse("drinks:target_update", kwargs={"pk": p.pk})
    content = client_logged.get(url).content.decode()

    assert f'name="quantity" value="{expect}"' in content


def test_target_update_load_form(client_logged):
    p = DrinkTargetFactory()

    url = reverse("drinks:target_update", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert url in actual


@pytest.mark.parametrize(
    "drink_type, ml, expect",
    [
        ("beer", 500, 2.5),
        ("wine", 750, 8),
        ("vodka", 1000, 40),
        ("stdav", 66, 66),
    ],
)
def test_target_update(drink_type, ml, expect, client_logged):
    p = DrinkTargetFactory()

    data = {"year": 1999, "quantity": ml, "drink_type": drink_type}
    url = reverse("drinks:target_update", kwargs={"pk": p.pk})
    client_logged.post(url, data)

    actual = models.DrinkTarget.objects.get(pk=p.pk)
    assert actual.quantity == expect


def test_target_update_not_load_other_user(client_logged, second_user):
    DrinkTargetFactory()
    obj = DrinkTargetFactory(quantity=666, user=second_user)

    url = reverse("drinks:target_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# SelectDrink View
def test_select_drink_redirect(client_logged):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})
    response = client_logged.get(url)

    assert response.status_code == 302
    assert response.url == reverse("drinks:index")


def test_select_drinks_set_drink_type(client_logged):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})
    client_logged.get(url)
    actual = User.objects.first()

    assert actual.drink_type == "wine"


def test_select_drinks_undeclared_drink_type_is_not_found(main_user, client_logged):
    main_user.drink_type = "wine"
    main_user.save()

    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "xxx"})
    response = client_logged.get(url)

    assert response.status_code == 404
    assert User.objects.first().drink_type == "wine"


@pytest.mark.parametrize(
    "tab, trigger",
    [
        pytest.param("trends", "reloadTrends", id="current_tab"),
        pytest.param("xxx", "reloadIndex", id="unknown_tab_falls_back_to_index"),
    ],
)
def test_select_drink_htmx_reloads_the_tab(client_logged, tab, trigger):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})
    response = client_logged.get(f"{url}?tab={tab}", HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert trigger in response.headers.get("HX-Trigger", "")
    assert User.objects.first().drink_type == "wine"


def _post_typical_year(client):
    # the form accepts only years the user has drinks in
    DrinkFactory(date=date(1998, 1, 1))
    DrinkFactory(date=date(1999, 1, 1))
    url = reverse("drinks:typical_year")
    return client.post(url, {"year_from": "1998", "year_to": "1999"})


@pytest.mark.parametrize(
    "send",
    [
        pytest.param(lambda c: c.get(reverse("drinks:index")), id="index"),
        pytest.param(lambda c: c.get(reverse("drinks:tab_habits")), id="habits"),
        pytest.param(lambda c: c.get(reverse("drinks:tab_trends")), id="trends"),
        pytest.param(lambda c: c.get(reverse("drinks:tab_risk")), id="risk"),
        pytest.param(
            lambda c: c.get(reverse("drinks:typical_year_last", kwargs={"qty": 3})),
            id="typical_year_last",
        ),
        pytest.param(_post_typical_year, id="typical_year_post"),
        pytest.param(
            lambda c: c.get(reverse("drinks:compare", kwargs={"qty": 1})),
            id="compare",
        ),
    ],
)
def test_a_user_with_no_year_raises(client_logged, main_user, send):
    main_user.year = None
    main_user.save()

    with pytest.raises(ValueError, match="has no year"):
        send(client_logged)
