import json
import re
from datetime import date
from types import SimpleNamespace

import pytest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _

from ...core.mixins import kwargs as core_kwargs
from ...core.tests.utils import (
    count_queries,
    form_posts_to,
    nav_tabs,
    setup_view,
    stat_card_edit_urls,
    stat_card_values,
    stat_cards,
    view_for,
)
from ...users.tests.factories import User
from .. import forms, models, views
from ..services.history import HistoryService
from ..services.index_tab import ConversionRowViewModel, StdAvViewModel
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
def test_tab_names_itself_in_the_browser_title(client_logged, headers):
    response = client_logged.get(reverse("drinks:tab_trends"), **headers)

    assert "<title>Gėrimai | Tendencijos</title>" in response.content.decode()


@pytest.mark.parametrize(
    "headers", [{"HX-Request": "true"}, {}], ids=["fragment", "page"]
)
def test_only_the_open_tab_reloads_on_its_trigger(client_logged, headers):
    content = client_logged.get("/drinks/data/", headers=headers).content.decode()

    listener = (
        'hx-get="/drinks/data/" hx-target="#tab_content" '
        'hx-trigger="reloadData from:body"'
    )
    assert listener in content
    assert content.count(" from:body") == 1


def test_index_takes_its_legend_position_from_the_paper_charts(client_logged):
    # chart_paper.js places every paper legend, so Drinks keeps no file of its own
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert re.search(r'<script[^>]* src="[^"]*js/chart_paper\.js"', content)
    assert not re.search(r'<script[^>]* src="[^"]*js/chart_drinks_legend\.js"', content)


def test_index_wraps_every_tab_in_the_paper_skin(client_logged):
    # the wrapper scopes the tokens every Drinks chart reads, so no other app's
    # page inherits them
    response = client_logged.get(reverse("drinks:index"))

    assert 'class="paper-skin"' in response.content.decode()


@pytest.mark.parametrize(
    "pattern",
    [
        # a drink is added from the bottom-pill widget, not from the nav
        pytest.param(r'<button type="button" class="quick-add__pill"', id="pill"),
        pytest.param(
            r'<form hx-post="/drinks/quick_add/"[^>]*hx-on::after:request="'
            r"if \(event\.detail\.ctx\.response\.raw\.ok\) "
            r"\{ Alpine\.\$data\(this\)\.open = false;",
            id="posts_and_closes_on_success",
        ),
        pytest.param(
            r'<input type="text" name="quantity"[^>]*x-model="quantity"',
            id="quantity_field",
        ),
        pytest.param(
            r'<div class="select-wrapper quick-add__type">\s*'
            r'<select name="option" class="form-select"\s*x-model="option"',
            id="drink_type_field",
        ),
        pytest.param(
            r'<form hx-post="/drinks/quick_add/".*?'
            r'<button type="submit" class="button-secondary">.*?</form>',
            id="submit",
        ),
        pytest.param(
            r'<button type="button" class="button-secondary"\s*'
            r'data-url="/drinks/TAB/new/"\s*'
            r"@click\.prevent=\"htmx\.ajax\('GET', \$el\.dataset\.url\.replace\('TAB', tab\)",
            id="more_opens_the_full_form_on_the_open_tab",
        ),
        # the sheet's state lives on the bar, so the pill and the sheet share one scope
        pytest.param(
            r'<div class="quick-add" id="quick-add" x-data="\{\s*open: false,',
            id="state_on_the_bar",
        ),
        pytest.param(
            r"x-data=\"\{[^\"]*defaults: "
            r"\{ beer: '1', wine: '150', vodka: '40', stdav: '1' \}",
            id="serving_defaults",
        ),
        pytest.param(
            r'<div class="quick-add" id="quick-add" x-data="[^"]*" '
            r'@keydown\.window\.escape="open = false">',
            id="escape_closes",
        ),
    ],
)
def test_index_quick_add_carries(client_logged, pattern):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert re.search(pattern, content, re.S)


@pytest.mark.parametrize(
    "absent, present",
    [
        # the quantity field's separator is a widget attribute, not an inline script
        pytest.param(
            r"<script(?![^>]* src=)[^>]*>(?:(?!</script>).)*input\.value\.replace",
            r"<script(?![^>]* src=)[^>]*>",
            id="inline_separator_script",
        ),
        # the page's own control is not an out-of-band copy of itself
        pytest.param(
            r'<div id="drink-type-control"[^>]*hx-swap-oob',
            r'<div id="drink-type-control"[^>]*>',
            id="switcher_swapped_out_of_band",
        ),
    ],
)
def test_index_carries_no(client_logged, absent, present):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert re.search(present, content, re.S)
    assert not re.search(absent, content, re.S)


def test_the_nav_draws_every_tab_in_order(client_logged):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert [name for name, _url in nav_tabs(content)] == [
        "index",
        "trends",
        "habits",
        "risk",
        "history",
        "data",
    ]


def test_index_renders_the_tab_nav_once(client_logged):
    # the nav sits outside #tab_content, so a tab swap cannot replace it
    response = client_logged.get(reverse("drinks:index"))

    assert response.content.decode().count('class="subnav"') == 1


def test_index_nav_tracks_the_open_tab_in_alpine(client_logged):
    # rendered once on Overview, so the mark moves client-side from there
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    habits = tab_button(content, "habits")
    assert '<div class="paper-skin" x-data="{ tab: \'index\' }">' in content
    assert "@click=\"tab = 'habits'\"" in habits
    assert ":class=\"{ active: tab === 'habits' }\"" in habits
    assert 'class="tab active"' in tab_button(content, "index")
    assert content.count('class="tab active"') == 1


def test_index_drink_type_links_carry_the_open_tab(client_logged):
    # not baked into the url: htmx reads it off the input at click time
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert '<input type="hidden" id="current-tab" name="tab" :value="tab">' in content
    assert (
        '<a class="dropdown-item button-sm" @click="$el.blur()"'
        ' href="/drinks/drink_type/wine/" hx-get="/drinks/drink_type/wine/"'
        ' hx-include="#current-tab"'
    ) in content


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

    assert re.search(
        r'<div class="quick-add" id="quick-add" x-data="\{\s*open: false,'
        r"\s*option: 'wine',",
        content,
    )
    assert '<option value="wine" selected>' in content
    assert '<option value="beer" selected>' not in content


def test_index_select_drink_drop_down_title(main_user, client_logged):
    main_user.drink_type = "wine"
    main_user.save()

    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert '<button class="dropdown__btn">Vynas</button>' in content


def test_index_drink_type_press_closes_the_menu(client_logged):
    # :focus-within holds the menu open, so the press has to drop the focus
    response = client_logged.get(reverse("drinks:index"))
    content = response.content.decode()

    assert content.count('@click="$el.blur()"') == len(models.DrinkType.values)


@pytest.mark.parametrize(
    "url_name, control",
    [
        pytest.param(
            "drinks:tab_trends",
            r'<div class="dropdown">\s*<button class="dropdown__btn">Vynas</button>',
            id="choice",
        ),
        pytest.param(
            "drinks:tab_risk",
            r'<span class="drink-type-fixed">',
            id="fixed",
        ),
    ],
)
def test_tab_reload_swaps_the_switcher_out_of_band(
    url_name, control, main_user, client_logged
):
    main_user.drink_type = "wine"
    main_user.save()

    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")

    oob = r'<div id="drink-type-control" hx-swap-oob="true">'
    assert re.search(oob + control, response.content.decode())


@pytest.mark.parametrize("url_name", ["drinks:tab_habits", "drinks:tab_risk"])
def test_tab_reading_std_av_says_the_whole_tab_is_in_it(url_name, client_logged):
    response = client_logged.get(reverse(url_name), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert (
        '<span class="drink-type-fixed">'
        '<span class="drink-type-note">Duomenys rodomi</span>'
        '<span class="drink-type-unit">[ Std Av ]</span>'
        "</span></div>"
    ) in content


def test_tab_choosing_the_unit_carries_no_caption(client_logged):
    response = client_logged.get(reverse("drinks:tab_trends"), HTTP_HX_REQUEST="true")

    assert '<span class="drink-type-note">' not in response.content.decode()


def test_tab_reading_no_amount_empties_the_control(client_logged):
    response = client_logged.get(reverse("drinks:tab_data"), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<div id="drink-type-control" hx-swap-oob="true"></div>' in content


# Tab urls
def tab_button(content: str, name: str) -> str:
    match = re.search(rf'<button\s+id="tab-{name}".*?</button>', content, re.S)

    assert match, f"no button rendered for the {name} tab"
    return match.group()


@pytest.mark.parametrize(
    "headers, whole",
    [
        pytest.param({}, True, id="page"),
        # the page a fragment lands in owns the nav and the bar
        pytest.param({"HTTP_HX_REQUEST": "true"}, False, id="fragment"),
        pytest.param(
            {"HTTP_HX_REQUEST": "true", "HTTP_HX_HISTORY_RESTORE_REQUEST": "true"},
            True,
            id="history_restore",
        ),
    ],
)
def test_tab_url_serves_the_whole_page_unless_htmx_swaps_it(
    client_logged, headers, whole
):
    content = client_logged.get(reverse("drinks:tab_risk"), **headers).content.decode()

    assert ('<div class="tabs" role="tablist"' in content) is whole
    assert ('<main id="tab_content"' in content) is whole
    assert ('<div class="quick-add" id="quick-add"' in content) is whole


def test_tab_url_opens_on_its_own_tab(client_logged):
    content = client_logged.get(reverse("drinks:tab_risk")).content.decode()

    assert '<div class="paper-skin" x-data="{ tab: \'risk\' }">' in content
    assert 'aria-selected="true"' in tab_button(content, "risk")


@pytest.mark.parametrize(
    "pattern",
    [
        pytest.param(r'\shx-get="/drinks/risk/"', id="fetches_its_url"),
        pytest.param(r'\shx-push-url="true"', id="pushes_its_url"),
        pytest.param(r'\shx-indicator="#indicator"', id="shows_the_loader"),
        pytest.param(r'\srole="tab"', id="is_a_tab"),
        pytest.param(r'\saria-controls="tab_content"', id="controls_the_panel"),
        pytest.param(r">\s*Rizikos\s*</button>", id="titled_by_its_tab"),
    ],
)
def test_a_tab_button(client_logged, pattern):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert re.search(pattern, tab_button(content, "risk"))


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
    "tab, charts, markup",
    [
        # One Drink: 1999-01-01 (a Friday), 1 Std Av of beer. A beer is 2.5 Std Av
        # and 500 ml, so the Drink is 0.4 beer and 200 ml.
        pytest.param(
            "index",
            [
                # 0.4 beer in January
                ("quantity", lambda p: p["data"][:2], [0.4, 0.0]),
                # 200 ml over January's 31 days
                ("consumption", lambda p: p["data"][:2], [6.45161, 0.0]),
            ],
            # the Converted table's rows exist only while the breakdown has data
            (
                r'<tr>\s*<td class="text-left">Alus, 0.5L</td>\s*<td class="main__figure">0,40</td>'
                r'(\s*<td class="main__figure">[^<]*</td>){3}\s*</tr>',
                r'<tr class="main__total">\s*<td class="text-left">Std Av</td>',
            ),
            id="index",
        ),
        pytest.param(
            "habits",
            [
                # Friday is the fifth weekday; 1999 has 53 of them, so 1 / 53 = 1.9 %
                (
                    "weekday",
                    lambda p: p["layers"][0]["drinking_day_share"][:6],
                    [0.0, 0.0, 0.0, 0.0, 1.9, 0.0],
                ),
                (
                    "weekday",
                    lambda p: p["layers"][0]["intensity"][:6],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                ),
            ],
            (),
            id="habits",
        ),
        pytest.param(
            "trends",
            [
                ("trend", lambda p: p["daily"][:2], [200.0, 0.0]),
                # 200 ml over a full window: 200 / 7 and 200 / 30, rounded to whole ml
                ("trend", lambda p: p["rolling_7"][:1], [29.0]),
                ("trend", lambda p: p["rolling_30"][:1], [7.0]),
            ],
            (),
            id="trends",
        ),
        pytest.param(
            "risk",
            [
                # the Friday sits in the week that starts on Monday 1998-12-28
                ("weekly", lambda p: p["categories"][:2], ["1998-12-28", "1999-01-04"]),
                ("weekly", lambda p: p["data"][:2], [1.0, 0.0]),
                # 1 Std Av is no Heavy day
                ("heavy", lambda p: p["data"][:2], [0, 0]),
            ],
            (),
            id="risk",
        ),
    ],
)
def test_tab_renders_its_charts(client_logged, tab, charts, markup):
    DrinkFactory()

    page = client_logged.get(reverse(TABS[tab])).content.decode()

    for chart, series, expect in charts:
        assert series(chart_data(page, chart)) == pytest.approx(expect, abs=1e-5)
    for row in markup:
        assert re.search(row, page)


def test_std_av_table_marks_the_total_row_by_its_state_not_its_title():
    rows = [
        ConversionRowViewModel("x Av", 1.0, 1.0, 1.0, 1.0, is_total=False),
        ConversionRowViewModel("Std vnt", 2.0, 2.0, 2.0, 2.0, is_total=True),
    ]

    html = render_to_string(
        "drinks/includes/tbl_std_av.html", {"ctx": StdAvViewModel(items=rows)}
    )

    assert re.search(r'<tr>\s*<td class="text-left">x Av</td>', html)
    assert re.search(
        r'<tr class="main__total">\s*<td class="text-left">Std vnt</td>', html
    )


@pytest.mark.parametrize(
    "tab, cards", [("index", 6), ("habits", 1), ("trends", 5), ("risk", 4)]
)
def test_tab_renders_its_cards(client_logged, tab, cards):
    DrinkFactory()

    page = client_logged.get(reverse(TABS[tab])).content.decode()

    assert len(stat_cards(page)) == cards


def test_back_reloads_the_page_rather_than_restoring_a_snapshot(client_logged):
    # htmx 4 has no ajax history restore, so Back is a plain page load
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert re.search(r'<div class="paper-skin"[^>]*x-data=', content)
    assert not re.search(r'<div class="paper-skin"[^>]*hx-history="false"', content)
    assert not re.search(
        r"<script[^>]*>(?:(?!</script>).)*htmx\.config\.refreshOnHistoryMiss",
        content,
        re.S,
    )


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


@pytest.mark.parametrize("url_name", TABS.values())
def test_tab_query_count_does_not_grow_with_the_drinks(client_logged, url_name):
    url = reverse(url_name)

    # the year read reaches back into last year, so both years grow
    for year in (1999, 1998):
        for i in range(2):
            DrinkFactory(date=date(year, 1, i + 1))
    two = count_queries(lambda: client_logged.get(url))

    for year in (1999, 1998):
        for i in range(2, 6):
            DrinkFactory(date=date(year, 1, i + 1))
    six = count_queries(lambda: client_logged.get(url))

    assert six == two


def test_tab_index_daily_limit_edit_link_uses_target_update(client_logged):
    target = DrinkTargetFactory()

    url = reverse("drinks:tab_index")
    response = client_logged.get(url)
    content = response.content.decode()

    edit_url = reverse("drinks:target_update", kwargs={"pk": target.pk})
    assert stat_card_edit_urls(content) == [edit_url]


@pytest.mark.parametrize(
    "factory, label, element",
    [
        pytest.param(DrinkTargetFactory, "Daily limit", "trend-card__edit", id="edit"),
        pytest.param(DrinkFactory, "Avg per day", "trend-card__info", id="info"),
    ],
)
def test_tab_index_meta_element_sits_above_the_unit(
    client_logged, factory, label, element
):
    factory()

    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    value = stat_card_values(content)[_(label)]
    assert value.index(element) < value.index("trend-card__unit")


def test_tab_index_renders_the_direction_arrow_in_its_own_element(client_logged):
    # the arrow is set below the figure's size, so it needs its own element;
    # Drinking days has a direction only with a year to compare against
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=8)

    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    value = stat_card_values(content)[_("Drinking days")]
    assert '<span class="trend-card__arrow">' in value


def test_tab_index_renders_the_state_modifier_for_a_compared_card(client_logged):
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=8)

    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    values = stat_card_values(content)
    assert values[_("Drinking days")].startswith(
        '<div class="trend-card__value trend-card__value--improving">'
    )
    assert [label for label, v in values.items() if 'value--"' in v] == []


def test_tab_index_renders_the_unit_apart_from_the_figure(client_logged):
    # the skin sets a unit at a third of the figure's size, so it needs an element
    DrinkFactory()

    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    value = stat_card_values(content)[_("Pure alcohol")]
    assert '<span class="trend-card__unit">L</span>' in value


def test_tab_index_omits_the_unit_element_when_there_is_no_unit(client_logged):
    DrinkFactory()

    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    values = stat_card_values(content)
    assert values
    assert [label for label, v in values.items() if 'unit"></span>' in v] == []


def test_tab_index_calendar_days_are_reachable_by_keyboard(client_logged):
    DrinkFactory(date=date(1999, 1, 5), stdav=2.5, option="beer")

    content = client_logged.get(reverse("drinks:tab_index")).content.decode()

    assert re.search(
        r'<i class="l\d"[^>]* role="img" tabindex="-1" aria-label="1999-01-05, ',
        content,
    )


def test_tab_index_htmx_fragment_carries_no_inline_script(client_logged):
    DrinkFactory(date=date(1999, 1, 5), stdav=2.5, option="beer")

    response = client_logged.get(reverse("drinks:tab_index"), HTTP_HX_REQUEST="true")
    fragment = response.content.decode("utf-8")

    opening_tags = re.findall(r"<script[^>]*>", fragment)

    assert '<div class="heat-card" id="heat-card">' in fragment
    assert opening_tags
    assert all('type="application/json"' in tag for tag in opening_tags)


def test_tab_index_loads_the_calendar_script_as_a_static_file(client_logged):
    DrinkFactory(date=date(1999, 1, 5), stdav=2.5, option="beer")

    response = client_logged.get(reverse("drinks:tab_index"))
    html = response.content.decode("utf-8")

    assert re.search(r'<script[^>]* src="[^"]*js/calendar\.js"', html)


# TypicalYearChart View
def test_tab_habits_loads_the_typical_year_chart(client_logged):
    # the container fetches itself, so the pooled range never depends on the tab
    response = client_logged.get(reverse("drinks:tab_habits"))
    content = response.content.decode()

    assert 'id="chart-typical-year-container"' in content
    assert f'hx-get="{reverse("drinks:typical_year")}"' in content
    assert 'id="typical-year-form"' in content


def control_buttons(content: str, controls: str) -> list[tuple[str, str]]:
    """(url, label) of each button from the `controls` row to its panel's end."""
    row = re.search(rf'<div class="{controls}">(.*?)</section>', content, re.S)

    assert row, f"no {controls} row rendered"
    return re.findall(r'<button [^>]*hx-get="([^"]*)"[^>]*>([^<]*)</button>', row[1])


def test_tab_habits_renders_the_pooled_range_presets(client_logged):
    # no preset for the header year alone: it is drawn in front already, so pooling
    # it would plot the same twelve months twice
    content = client_logged.get(reverse("drinks:tab_habits")).content.decode()

    assert control_buttons(content, "pool-controls") == [
        ("/drinks/typical_year/all/", "Visi metai"),
        ("/drinks/typical_year/2/", "2 metų"),
        ("/drinks/typical_year/3/", "3 metų"),
        ("/drinks/typical_year/5/", "5 metų"),
        ("/drinks/typical_year/", "Išvalyti"),
    ]


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


def view_today(mocker, today):
    mocker.patch.object(core_kwargs, "date", mocker.Mock(today=lambda: today))


def test_every_figure_stops_at_the_views_today(client_logged, mocker):
    view_today(mocker, date(1999, 3, 1))
    DrinkFactory(date=date(1998, 1, 1), stdav=2.5)
    DrinkFactory(date=date(1999, 1, 15), stdav=2.5)
    DrinkFactory(date=date(1999, 3, 1), stdav=2.5)
    DrinkFactory(date=date(1999, 4, 10), stdav=2.5)

    index = client_logged.get(reverse("drinks:tab_index")).content.decode()
    typical = client_logged.get(reverse("drinks:typical_year")).content.decode()
    compare = client_logged.get(reverse("drinks:compare", kwargs={"qty": 1}))
    months = chart_data(compare.content.decode(), "history")["series"][0]["data"]
    history = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert ("Blaivios dienos", "0", "1999-03-01") in stat_cards(index)
    assert len(chart_data(typical, "typical-year")["layers"][0]["intensity"]) == 3
    assert len(months) == 3
    # 7.5 Std Av of beer over Jan 1 to Mar 1, the 60 days the view has reached
    assert chart_data(history, "summary")["data_ml"][-1] == 25.0


def test_tab_risk_heavy_panel_leaves_the_threshold_to_its_chart(client_logged):
    content = client_logged.get(reverse("drinks:tab_risk")).content.decode()

    assert "panel__subtitle" not in content


def test_tab_index_renders_each_explanation_part_as_its_own_paragraph(
    client_logged, mocker
):
    view_today(mocker, date(1999, 6, 1))
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=7)

    content = client_logged.get(
        reverse("drinks:tab_index"), HTTP_HX_REQUEST="true"
    ).content.decode()

    card = re.search(
        r'<div class="trend-card__label">Vartojimo dienos</div>'
        r'.*?<span class="trend-card__info"[^>]* aria-label="([^"]*)"'
        r'.*?<span class="trend-card__explanation" role="tooltip">(.*?)</span>',
        content,
        re.S,
    )
    assert card, "no Vartojimo dienos Card with an explanation"
    parts = (
        "1% metų dienų iki šiandien",
        "Kalendorinės dienos, kuriomis užfiksuotas bent vienas vartojimas.",
        "Rodyklė lygina su pernai iki tos pačios datos.",
    )
    assert card[2] == "".join(f"<p>{part}</p>" for part in parts)
    # a label cannot hold markup, so it stays the parts run together
    assert card[1] == " ".join(parts)


# TabData View
@pytest.mark.parametrize(
    "url_name, drink_dates, message",
    [
        pytest.param(
            "drinks:tab_data",
            [date(2020, 1, 2)],
            "1999 metais įrašų nėra.",
            id="data",
        ),
        # History runs every year from the first Drink to today, so any Drink fills it
        pytest.param(
            "drinks:tab_history",
            [],
            _("Data are missing. At least two years of data is required."),
            id="history",
        ),
    ],
)
def test_an_empty_tab_draws_the_paper_notice(
    client_logged, url_name, drink_dates, message
):
    for drink_date in drink_dates:
        DrinkFactory(date=drink_date)

    content = client_logged.get(reverse(url_name)).content.decode("utf-8")

    assert re.search(rf'<div class="alert">\s*{re.escape(message)}\s*</div>', content)


def test_tab_data(client_logged):
    p = DrinkFactory(stdav=47.5)
    response = client_logged.get(reverse("drinks:tab_data"))

    actual = response.content.decode("utf-8")

    assert '<td class="text-left main__figure">19,0 vnt</td>' in actual
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

    assert '<td class="text-left main__figure">500 ml</td>' in actual


# TabHistory View
def test_tab_history_renders_the_summary_chart_data(client_logged):
    DrinkFactory()

    page = client_logged.get(reverse("drinks:tab_history")).content.decode()

    payload = chart_data(page, "summary")

    # the one Drink is in 1999: 200 ml over its 365 days, and 10 g of pure alcohol
    assert payload["categories"][:2] == [1999, 2000]
    assert payload["data_ml"][:2] == pytest.approx([0.54795, 0.0], abs=1e-5)
    assert payload["data_alcohol"][:2] == pytest.approx([0.01, 0.0], abs=1e-5)


def test_tab_history_titles_its_panels(client_logged):
    DrinkFactory()
    content = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert f'<h2 class="panel__title">{_("Drinks")}</h2>' in content
    assert f'<h2 class="panel__title">{_("Year comparison")}</h2>' in content


def compare_form(content: str) -> str:
    """The year-pair form, from its opening tag to its close."""
    form = re.search(r'<form id="compare-form".*?</form>', content, re.S)

    assert form, "no compare form rendered"
    return form.group()


def test_tab_history_has_unified_compare_panel(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    content = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert control_buttons(content, "compare-controls") == [
        ("/drinks/compare/2/", "2 metų"),
        ("/drinks/compare/3/", "3 metų"),
        ("/drinks/compare/7/", "7 metų"),
    ]
    assert re.match(
        r'<form id="compare-form"[^>]* hx-post="/drinks/compare/"'
        r' hx-target="#chart-history-container"',
        compare_form(content),
    )
    assert 'id="compare-form-and-chart"' not in content
    assert "chart-compare-two" not in content


def test_tab_history_chart_auto_loads_default_comparison(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    content = client_logged.get(reverse("drinks:tab_history")).content.decode()

    assert (
        '<div id="chart-history-container" hx-get="/drinks/compare/2/"'
        ' hx-trigger="load">'
    ) in content


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
    content = client_logged.get(reverse("drinks:compare_two")).content.decode()

    form = compare_form(content)
    assert re.match(r'<form id="compare-form"[^>]* hx-post="/drinks/compare/"', form)
    assert re.search(r'<input [^>]*name="year1"', form)
    assert re.search(r'<input [^>]*name="year2"', form)


def test_compare_data_includes_form_and_oob_swap(client_logged):
    DrinkFactory()

    url = reverse("drinks:compare", kwargs={"qty": 2})
    content = client_logged.get(url).content.decode()

    assert re.match(
        r'<form id="compare-form"[^>]* hx-swap-oob="true">', compare_form(content)
    )


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
        pytest.param(
            views.New, "drinks:new", "history", "reloadHistory", id="new_history"
        ),
        pytest.param(views.New, "drinks:new", "xxx", "reloadData", id="new_unknown"),
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
    "factory, url_name, data, trigger",
    [
        (
            DrinkFactory,
            "drinks:update",
            {"date": "1999-01-01", "stdav": 0.68, "option": "beer"},
            '{"reloadData": {}}',
        ),
        (DrinkFactory, "drinks:delete", {}, '{"reloadData": {}}'),
        (
            DrinkTargetFactory,
            "drinks:target_update",
            {"year": 1999, "quantity": 100, "drink_type": "beer"},
            '{"reloadIndex": {}}',
        ),
    ],
    ids=["update", "delete", "target_update"],
)
def test_an_edit_reloads_the_tab_its_row_is_on(
    factory, url_name, data, trigger, client_logged
):
    url = reverse(url_name, kwargs={"pk": factory().pk})

    response = client_logged.post(url, data, headers={"HX-Request": "true"})

    assert response.headers["HX-Trigger"] == trigger


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
        ("history", "history"),
        ("xxx", "index"),
    ],
)
def test_new_load_form(client_logged, mocker, url_name, field, tab, posts_to):
    view_today(mocker, date(2000, 1, 1))

    url = reverse(url_name, kwargs={"tab": tab})
    content = client_logged.get(url).content.decode()

    posted = reverse(url_name, kwargs={"tab": posts_to})
    assert form_posts_to(content, "generic-form", posted)
    assert field in content


def test_new_tab_data(client_logged):
    data = {"date": "1999-01-01", "stdav": 19, "option": "beer"}
    url = reverse("drinks:new", kwargs={"tab": "data"})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()
    drink = models.Drink.objects.get()

    assert '<td class="text-left main__figure">19,0 vnt</td>' in actual
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

    assert '<td class="text-left main__figure">0,7 vnt</td>' in actual
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


@pytest.mark.parametrize(
    "url_name, factory",
    [
        pytest.param("drinks:update", DrinkFactory, id="drink_update"),
        pytest.param("drinks:delete", DrinkFactory, id="drink_delete"),
        pytest.param("drinks:target_update", DrinkTargetFactory, id="target_update"),
    ],
)
def test_another_users_object_is_not_found(
    client_logged, second_user, url_name, factory
):
    factory()
    obj = factory(user=second_user)

    response = client_logged.get(reverse(url_name, kwargs={"pk": obj.pk}))

    assert response.status_code == 404


# Drink Delete
def test_view_drinks_delete_load_form(client_logged):
    p = DrinkFactory()

    url = reverse("drinks:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url, {})
    actual = response.content.decode()

    assert form_posts_to(actual, "delete-form", url)
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01, beer, 200ml</strong>?" in actual
    )


def test_view_drinks_delete(client_logged):
    p = DrinkFactory()

    assert models.Drink.objects.all().count() == 1
    url = reverse("drinks:delete", kwargs={"pk": p.pk})
    client_logged.post(url)

    assert models.Drink.objects.all().count() == 0


def test_drinks_delete_other_user_post_form(client_logged, second_user):
    obj = DrinkFactory(user=second_user)

    url = reverse("drinks:delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert models.Drink.objects.all().count() == 1


# Target Create/Update
@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            lambda: reverse("drinks:target_new", kwargs={"tab": "index"}), id="new"
        ),
        pytest.param(
            lambda: reverse(
                "drinks:target_update", kwargs={"pk": DrinkTargetFactory().pk}
            ),
            id="update",
        ),
    ],
)
def test_target_saves_the_quantity_in_std_av(client_logged, url):
    data = {"year": 1999, "quantity": 750, "drink_type": "wine"}
    client_logged.post(url(), data)

    actual = models.DrinkTarget.objects.get()
    assert (actual.drink_type, actual.quantity) == ("wine", 8)


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

    assert form_posts_to(response.content.decode(), "generic-form", url)


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
    "query, trigger",
    [
        pytest.param("?tab=trends", "reloadTrends", id="current_tab"),
        pytest.param("?tab=xxx", "reloadIndex", id="unknown_tab_falls_back_to_index"),
        pytest.param("", "reloadIndex", id="no_tab_falls_back_to_index"),
    ],
)
def test_select_drink_htmx_reloads_the_tab(client_logged, query, trigger):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})
    response = client_logged.get(f"{url}{query}", HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert trigger in response.headers.get("HX-Trigger", "")
    assert User.objects.first().drink_type == "wine"


def _typical_year_last(view):
    return view.get(view.request)


def _typical_year_post(view):
    form = SimpleNamespace(cleaned_data={"year_from": 1998, "year_to": 1999})
    return view.form_valid(form)


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabIndex).get_context_data(), id="index"
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabHabits).get_context_data(),
            id="habits",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabTrends).get_context_data(),
            id="trends",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabRisk).get_context_data(), id="risk"
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabData).get_queryset(), id="data"
        ),
        pytest.param(
            lambda rf, u: _typical_year_last(
                view_for(rf, u, views.TypicalYearChart, qty=3)
            ),
            id="typical_year_last",
        ),
        pytest.param(
            lambda rf, u: _typical_year_post(view_for(rf, u, views.TypicalYearChart)),
            id="typical_year_post",
        ),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.Compare, qty=1).get_context_data(),
            id="compare",
        ),
        pytest.param(
            lambda rf, u: HistoryService(u, [], date(2025, 1, 1)), id="history_service"
        ),
        pytest.param(
            lambda rf, u: forms.DrinkTargetForm(user=u, today=date(2025, 1, 1)),
            id="target_form",
        ),
        pytest.param(
            lambda rf, u: forms.DrinkCompareForm(user=u, today=date(2025, 1, 1)),
            id="compare_form",
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, mocker, call):
    main_user.year = None
    # render() runs the context processors, which raise on a no-year user themselves
    mocker.patch.object(views, "render")

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)
