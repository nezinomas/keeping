import re
from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse, reverse_lazy
from django.utils.html import escape
from django.utils.translation import gettext as _

from ...core.tests.utils import setup_view
from ...users.tests.factories import User
from .. import forms, models, views
from .factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                             IndexView
# -------------------------------------------------------------------------------------
def test_index_func():
    view = resolve("/drinks/")
    assert views.TabIndex == view.func.view_class


def test_index_200(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_loads_the_shared_chart_legend_defaults(client_logged):
    # every Drinks chart reads its legend position from this one file, so the
    # page dropping it would put every legend back in the theme's top corner
    response = client_logged.get(reverse("drinks:index"))

    assert "js/chart_drinks_legend.js" in response.content.decode()


def test_index_wraps_every_tab_in_the_paper_skin(client_logged):
    # the wrapper scopes the tokens every Drinks chart reads, so no other app's
    # page inherits them
    response = client_logged.get(reverse("drinks:index"))

    assert 'class="paper-skin"' in response.content.decode()


def test_index_loads_the_paper_chart_theme(client_logged):
    # the shared Highcharts theme is every other app's too, so the paper
    # overrides ride in a file only the pages wearing the skin load
    response = client_logged.get(reverse("drinks:index"))

    assert "js/chart_paper.js" in response.content.decode()


def test_index_quick_add(client_logged):
    # adding a drink now happens via the persistent quick-add widget
    # (bottom pill -> sheet) instead of a button in the nav
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
    assert "event.detail.xhr" in content
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


@pytest.mark.parametrize(
    "tab",
    ["tab_index", "tab_habits", "tab_trends", "tab_risk", "tab_history", "tab_data"],
)
def test_tabs_do_not_render_the_nav(tab, client_logged):
    # a tab response is the body only; the page it lands in owns the nav
    response = client_logged.get(reverse(f"drinks:{tab}"), HTTP_HX_REQUEST="true")

    assert 'class="subnav"' not in response.content.decode()


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


def test_index_switcher_is_not_swapped_out_of_band(client_logged):
    """The page draws the control itself; only a tab reload replaces it."""
    response = client_logged.get(reverse("drinks:index"))

    assert "hx-swap-oob" not in response.content.decode()


def test_index_context(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)
    context = response.context

    assert "drink_types" in context
    assert context["drink_types"].selected == "beer"
    assert context["drink_type_control"].selected == "beer"


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
    "tab, expect",
    [
        ("index", "Vynas"),
        ("trends", "Vynas"),
        ("history", "Vynas"),
        ("habits", "Std Av"),
        ("risk", "Std Av"),
    ],
)
def test_tab_reload_swaps_the_switcher_out_of_band(
    tab, expect, main_user, client_logged
):
    """A tab arrives with the control its own readings are in."""
    main_user.drink_type = "wine"
    main_user.save()

    response = client_logged.get(reverse(f"drinks:tab_{tab}"), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<div id="drink-type-control" hx-swap-oob="true">' in content
    assert expect in content


@pytest.mark.parametrize("tab", ["habits", "risk"])
def test_tab_reading_std_av_names_the_unit_and_offers_no_choice(tab, client_logged):
    response = client_logged.get(reverse(f"drinks:tab_{tab}"), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<span class="drink-type-unit">[ Std Av ]</span>' in content
    assert "dropdown" not in content


@pytest.mark.parametrize("tab", ["habits", "risk"])
def test_tab_reading_std_av_says_the_whole_tab_is_in_it(tab, client_logged):
    """A unit with no choice beside it has to say why it is there, and the
    caption is part of that one control — not a label sitting next to it."""
    response = client_logged.get(reverse(f"drinks:tab_{tab}"), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert (
        '<span class="drink-type-fixed">'
        '<span class="drink-type-note">Duomenys rodomi</span>'
        '<span class="drink-type-unit">[ Std Av ]</span>'
        "</span>"
    ) in content


@pytest.mark.parametrize("tab", ["index", "trends", "history"])
def test_tab_choosing_the_unit_carries_no_caption(tab, client_logged):
    """The switcher says what it is by being pressable."""
    response = client_logged.get(reverse(f"drinks:tab_{tab}"), HTTP_HX_REQUEST="true")

    assert _("Data shown as") not in response.content.decode()


def test_tab_reading_no_amount_empties_the_control(client_logged):
    response = client_logged.get(reverse("drinks:tab_data"), HTTP_HX_REQUEST="true")
    content = response.content.decode()

    assert '<div id="drink-type-control" hx-swap-oob="true"></div>' in content


@pytest.mark.parametrize("tab", ["index", "trends", "history", "habits", "risk"])
def test_tab_context_carries_the_control(tab, client_logged):
    response = client_logged.get(reverse(f"drinks:tab_{tab}"))

    assert response.context["drink_type_control"].state in ("choice", "fixed")


def test_tab_context_carries_a_control_that_draws_nothing(client_logged):
    """Never None — the tab that reads no amount still answers every question
    the template asks."""
    response = client_logged.get(reverse("drinks:tab_data"))

    assert response.context["drink_type_control"].state == "absent"


# -------------------------------------------------------------------------------------
#                                                                          Tab urls
# -------------------------------------------------------------------------------------
TABS = ["index", "trends", "habits", "risk", "history", "data"]


def tab_button(content: str, name: str) -> str:
    """The attributes of one tab button, so a test does not pin their order."""
    match = re.search(rf'<button\s+id="tab-{name}"(.*?)>', content, re.S)

    assert match, f"no button rendered for the {name} tab"
    return match.group(1)


@pytest.mark.parametrize("tab", TABS)
def test_tab_url_opens_the_whole_page(tab, client_logged):
    """A pushed url has to answer a bookmark and a reload, not just a swap."""
    response = client_logged.get(reverse(f"drinks:tab_{tab}"))
    content = response.content.decode()

    assert 'role="tablist"' in content
    assert 'id="quick-add"' in content


@pytest.mark.parametrize("tab", TABS)
def test_tab_url_opens_on_its_own_tab(tab, client_logged):
    response = client_logged.get(reverse(f"drinks:tab_{tab}"))
    content = response.content.decode()

    assert f"{{ tab: '{tab}' }}" in content
    assert 'aria-selected="true"' in tab_button(content, tab)


@pytest.mark.parametrize("tab", TABS)
def test_tab_url_over_htmx_is_only_the_fragment(tab, client_logged):
    response = client_logged.get(reverse(f"drinks:tab_{tab}"), HTTP_HX_REQUEST="true")

    assert 'role="tablist"' not in response.content.decode()


def test_tab_url_restoring_history_is_the_whole_page(client_logged):
    """Back asks over htmx too, and swaps what comes back into the whole body."""
    response = client_logged.get(
        reverse("drinks:tab_risk"),
        HTTP_HX_REQUEST="true",
        HTTP_HX_HISTORY_RESTORE_REQUEST="true",
    )

    assert 'role="tablist"' in response.content.decode()


@pytest.mark.parametrize("tab", TABS)
def test_tab_button_pushes_its_url(tab, client_logged):
    attrs = tab_button(client_logged.get(reverse("drinks:index")).content.decode(), tab)

    assert f'hx-get="/drinks/{tab}/"' in attrs
    assert 'hx-push-url="true"' in attrs


@pytest.mark.parametrize("tab", TABS)
def test_tab_button_shows_the_loader_while_it_fetches(tab, client_logged):
    attrs = tab_button(client_logged.get(reverse("drinks:index")).content.decode(), tab)

    assert 'hx-indicator="#indicator"' in attrs


@pytest.mark.parametrize("tab", TABS)
def test_every_tab_button_is_a_tab(tab, client_logged):
    attrs = tab_button(client_logged.get(reverse("drinks:index")).content.decode(), tab)

    assert 'role="tab"' in attrs
    assert 'aria-controls="tab_content"' in attrs


def test_only_the_open_tab_is_selected(client_logged):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert 'aria-selected="true"' in tab_button(content, "index")
    assert all('aria-selected="false"' in tab_button(content, t) for t in TABS[1:])


def test_the_open_tab_is_the_only_one_in_the_focus_order(client_logged):
    """Arrow keys move between tabs, so Tab enters the row once and leaves it."""
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert 'tabindex="0"' in tab_button(content, "index")
    assert all('tabindex="-1"' in tab_button(content, t) for t in TABS[1:])


def test_back_reloads_the_page_rather_than_restoring_a_snapshot(client_logged):
    """htmx restores a snapshot by replacing the body, which runs every script in
    it twice — `modal.js` dies on a redeclared constant. Never snapshotting turns
    Back into a miss, and a miss into a plain page load."""
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert 'hx-history="false"' in content
    assert "htmx.config.refreshOnHistoryMiss = true" in content


def test_the_tabs_carry_a_tablist(client_logged):
    content = client_logged.get(reverse("drinks:index")).content.decode()

    assert 'role="tablist"' in content
    assert 'role="tabpanel"' in content


# -------------------------------------------------------------------------------------
#                                                                         TabIndex View
# -------------------------------------------------------------------------------------
def test_tab_index_func():
    view = resolve("/drinks/index/")
    assert views.TabIndex == view.func.view_class


def test_tab_index_200(client_logged):
    url = reverse("drinks:tab_index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_index_context(client_logged):
    DrinkFactory()

    url = reverse("drinks:tab_index")
    response = client_logged.get(url)

    assert "all_years" in response.context
    assert "chart_quantity" in response.context
    assert "chart_consumption" in response.context
    assert "tbl_std_av" in response.context
    assert "cards" in response.context
    assert "calendar" in response.context


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
    """The pencil and the unit share one column beside the figure, the pencil on
    top — so both live in the card's meta stack, the pencil first."""
    DrinkTargetFactory()

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    meta = re.search(r'<span class="trend-card__meta">(.*?)</div>', content, re.S)
    assert meta
    assert meta.group(1).index("trend-card__edit") < meta.group(1).index(
        "trend-card__unit"
    )


def test_tab_index_info_icon_sits_above_the_unit(client_logged):
    """A Stat Card's information mark shares the meta stack with the unit, above
    it, rather than trailing the figure."""
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
    """The arrow is set well below the figure's size, so it needs its own
    element rather than sitting in the value as a bare entity."""
    # Drinking days only carries a direction once there is a year to compare
    # against, so the arrow needs both years on record
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=8)

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    assert 'class="trend-card__arrow"' in content


@time_machine.travel("1999-06-01")
def test_tab_index_renders_the_state_modifier_for_a_compared_card(client_logged):
    """A comparison resolves its state from the direction rather than storing
    one, so the template has to reach a property to colour it."""
    DrinkFactory(date=date(1999, 1, 10), stdav=7)
    DrinkFactory(date=date(1998, 1, 10), stdav=8)

    response = client_logged.get(reverse("drinks:tab_index"))
    content = response.content.decode()

    assert 'class="trend-card__value trend-card__value--improving"' in content
    assert 'trend-card__value--"' not in content


def test_tab_index_renders_the_unit_apart_from_the_figure(client_logged):
    """The skin sets a unit at a third of the figure's size, so it needs its own
    element rather than trailing the value as text."""
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


# -------------------------------------------------------------------------------------
#                                                                        TabHabits View
# -------------------------------------------------------------------------------------
def test_tab_habits_func():
    view = resolve("/drinks/habits/")

    assert views.TabHabits == view.func.view_class


def test_tab_habits_200(client_logged):
    url = reverse("drinks:tab_habits")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_habits_context_tab_value(client_logged):
    url = reverse("drinks:tab_habits")
    response = client_logged.get(url)

    assert response.context["tab"] == "habits"


def test_tab_habits_context(client_logged):
    url = reverse("drinks:tab_habits")
    response = client_logged.get(url)

    assert "chart_weekday" in response.context
    assert "cards" in response.context


# -------------------------------------------------------------------------------------
#                                                                 TypicalYearChart View
# -------------------------------------------------------------------------------------
def test_typical_year_func():
    view = resolve("/drinks/typical_year/")

    assert views.TypicalYearChart is view.func.view_class


def test_typical_year_200(client_logged):
    response = client_logged.get(reverse("drinks:typical_year"))

    assert response.status_code == 200


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

    chart = client_logged.get(reverse("drinks:typical_year")).context["chart"]

    assert chart.year.label == "1999"
    assert not chart.pooled.has_data
    assert chart.layers == [chart.year]


def test_typical_year_invalid_retargets_form(client_logged):
    url = reverse("drinks:typical_year")
    response = client_logged.post(url, {"year_from": "2005", "year_to": "1999"})

    assert response["HX-Retarget"] == "#typical-year-form"
    assert response["HX-Reswap"] == "outerHTML"
    assert not response.context["form"].is_valid()
    assert "chart-typical-year-data" not in response.content.decode()


# -------------------------------------------------------------------------------------
#                                                                        TabTrends View
# -------------------------------------------------------------------------------------
def test_tab_trends_func():
    view = resolve("/drinks/trends/")

    assert views.TabTrends == view.func.view_class


def test_tab_trends_200(client_logged):
    url = reverse("drinks:tab_trends")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_trends_context_tab_value(client_logged):
    url = reverse("drinks:tab_trends")
    response = client_logged.get(url)

    assert response.context["tab"] == "trends"


def test_tab_trends_context(client_logged):
    url = reverse("drinks:tab_trends")
    response = client_logged.get(url)

    assert "chart_trend" in response.context
    assert "cards" in response.context


# -------------------------------------------------------------------------------------
#                                                                         TabRisk View
# -------------------------------------------------------------------------------------
def test_tab_risk_func():
    view = resolve("/drinks/risk/")

    assert views.TabRisk == view.func.view_class


def test_tab_risk_200(client_logged):
    url = reverse("drinks:tab_risk")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_risk_context_tab_value(client_logged):
    url = reverse("drinks:tab_risk")
    response = client_logged.get(url)

    assert response.context["tab"] == "risk"


def test_tab_risk_context(client_logged):
    url = reverse("drinks:tab_risk")
    response = client_logged.get(url)

    assert "chart_weekly" in response.context
    assert "chart_heavy" in response.context
    assert "cards" in response.context


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


# -------------------------------------------------------------------------------------
#                                                                          TabData View
# -------------------------------------------------------------------------------------
def test_tab_data_func():
    view = resolve("/drinks/data/")

    assert views.TabData == view.func.view_class


def test_tab_data_200(client_logged):
    url = reverse("drinks:tab_data")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_data_context(client_logged):
    url = reverse("drinks:tab_data")
    response = client_logged.get(url)

    assert "object_list" in response.context


def test_tab_data_empty_current_year(client_logged):
    DrinkFactory(date=date(2020, 1, 2))

    url = reverse("drinks:tab_data")
    response = client_logged.get(url)

    assert "<b>1999</b> metais įrašų nėra." in response.content.decode("utf-8")


def test_tab_data(client_logged):
    p = DrinkFactory(stdav=47.5)
    response = client_logged.get(reverse("drinks:tab_data"))

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert "19,0" in actual
    assert f'<a role="button" hx-get="/drinks/update/{p.pk}/"' in actual
    assert f'<a role="button" hx-get="/drinks/delete/{p.pk}/"' in actual


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

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert "500 ml" in actual


# -------------------------------------------------------------------------------------
#                                                                       TabHistory View
# -------------------------------------------------------------------------------------
def test_tab_history_func():
    view = resolve("/drinks/history/")

    assert views.TabHistory == view.func.view_class


def test_tab_history_200(client_logged):
    url = reverse("drinks:tab_history")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_tab_history_context_tab_value(client_logged):
    url = reverse("drinks:tab_history")
    response = client_logged.get(url)

    assert response.context["tab"] == "history"


def test_tab_history_context(client_logged):
    DrinkFactory()

    url = reverse("drinks:tab_history")
    response = client_logged.get(url)

    assert "categories" in response.context["chart"]
    assert "data_ml" in response.context["chart"]
    assert "data_alcohol" in response.context["chart"]


@time_machine.travel("1999-1-1")
def test_tab_history_has_unified_compare_panel(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    url = reverse("drinks:tab_history")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    # the unified year-comparison panel lives on the History tab
    assert 'id="historical-data"' in content
    assert 'id="chart-history-container"' in content

    # preset buttons target the single history chart
    assert f'hx-get="{reverse("drinks:compare", kwargs={"qty": 2})}"' in content
    assert f'hx-get="{reverse("drinks:compare", kwargs={"qty": 3})}"' in content
    assert f'hx-get="{reverse("drinks:compare", kwargs={"qty": 7})}"' in content
    assert "Visi metai" not in content
    assert "All years" not in content

    # the year-comparison form is embedded (not lazy-loaded) and posts to the
    # same shared chart
    assert 'id="compare-form"' in content
    assert f'hx-post="{reverse("drinks:compare_two")}"' in content
    assert 'hx-target="#chart-history-container"' in content

    # the second overlay chart/container is gone (one unified chart)
    assert 'id="compare-form-and-chart"' not in content
    assert "chart-compare-two" not in content


@time_machine.travel("1999-1-1")
def test_tab_history_chart_auto_loads_default_comparison(client_logged):
    DrinkFactory()
    DrinkFactory(date=date(1988, 1, 1))

    url = reverse("drinks:tab_history")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    # the shared chart fills itself on load with the 2-year preset
    assert 'hx-trigger="load"' in content


def test_tab_history_hides_compare_panel_without_records(client_logged):
    url = reverse("drinks:tab_history")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    # with no records the comparison panel is not rendered
    assert 'id="historical-data"' not in content
    assert 'id="chart-history-container"' not in content
    assert 'id="compare-form"' not in content


# -------------------------------------------------------------------------------------
#                                                                          Compare View
# -------------------------------------------------------------------------------------
def test_compare_data_func():
    view = resolve("/drinks/compare/1/")

    assert views.Compare is view.func.view_class


def test_compare_data_200(client_logged):
    DrinkFactory()

    url = reverse("drinks:compare", kwargs={"qty": 2})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_compare_data_chart(client_logged):
    DrinkFactory(stdav=2.5)

    url = reverse("drinks:compare", kwargs={"qty": 2})
    response = client_logged.get(url)
    actual = response.context["chart"]

    assert response.status_code == 200
    assert actual.title  # chart carries a title for Highcharts to render
    assert actual.serries[0]["name"] == 1999
    assert round(actual.serries[0]["data"][0], 2) == 16.13


# -------------------------------------------------------------------------------------
#                                                                       CompareTwo View
# -------------------------------------------------------------------------------------
def test_comparetwo_func():
    view = resolve("/drinks/compare/")

    assert views.CompareTwo is view.func.view_class


def test_comparetwo_200(client_logged):
    response = client_logged.get("/drinks/compare/")

    assert response.status_code == 200


def test_compare_data_includes_form_and_oob_swap(client_logged):
    DrinkFactory()

    url = reverse("drinks:compare", kwargs={"qty": 2})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert "form" in response.context
    assert isinstance(response.context["form"], forms.DrinkCompareForm)
    assert 'id="compare-form"' in content
    assert 'hx-swap-oob="true"' in content


def test_comparetwo_invalid_retargets_form(client_logged):
    url = reverse("drinks:compare_two")
    response = client_logged.post(url, {"year1": "1999", "year2": "2000"})

    # an invalid submit re-renders the form in place, leaving the chart untouched
    assert response["HX-Retarget"] == "#compare-form"
    assert response["HX-Reswap"] == "outerHTML"
    assert not response.context["form"].is_valid()


# -------------------------------------------------------------------------------------
#                                                                         Create/Update
# -------------------------------------------------------------------------------------
def test_new_func():
    view = resolve("/drinks/index/new/")

    assert views.New is view.func.view_class


def test_update_func():
    view = resolve("/drinks/update/1/")

    assert views.Update is view.func.view_class


@pytest.mark.parametrize(
    "tab, trigger",
    [
        ("index", "reloadIndex"),
        ("data", "reloadData"),
        ("history", "reloadHistory"),
        ("xxx", "reloadData"),
    ],
)
def test_trigger_name(tab, trigger, rf):
    request = rf.get(reverse("drinks:new", kwargs={"tab": tab}))

    view = setup_view(views.New(), request)
    view.kwargs = {"tab": tab}
    actual = view.get_hx_trigger_django()

    assert actual == trigger


@pytest.mark.parametrize(
    "tab, expect_url",
    [
        ("index", reverse_lazy("drinks:new", kwargs={"tab": "index"})),
        ("data", reverse_lazy("drinks:new", kwargs={"tab": "data"})),
        ("history", reverse_lazy("drinks:new", kwargs={"tab": "history"})),
        ("xxx", reverse_lazy("drinks:new", kwargs={"tab": "index"})),
    ],
)
@time_machine.travel("2000-1-1")
def test_new_load_form(client_logged, tab, expect_url):
    url = reverse("drinks:new", kwargs={"tab": tab})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{expect_url}"' in actual
    assert '<input type="text" name="date" value="1999-01-01"' in actual


def test_new_tab_data(client_logged):
    data = {"date": "1999-01-01", "stdav": 19, "option": "beer"}
    url = reverse("drinks:new", kwargs={"tab": "data"})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()

    assert "19" in actual
    assert '<a role="button" hx-get="/drinks/update/1/"' in actual


def test_new_invalid_data(client_logged):
    data = {"date": -2, "stdav": "x"}
    url = reverse("drinks:new", kwargs={"tab": "data"})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_update(client_logged):
    p = DrinkFactory()

    data = {"date": "1999-01-01", "stdav": 0.68, "option": "beer"}
    url = reverse("drinks:update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode()

    assert url in actual
    assert "0,7 vnt" in actual
    assert f'<a role="button" hx-get="/drinks/update/{p.pk}/"' in actual


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
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.initial["stdav"] == expect


def test_drinks_update_not_load_other_user(client_logged, second_user):
    DrinkFactory()
    obj = DrinkFactory(date=date(1111, 1, 1), stdav=0.666, user=second_user)

    url = reverse("drinks:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# -------------------------------------------------------------------------------------
#                                                                          Drink Delete
# -------------------------------------------------------------------------------------
def test_view_drinks_delete_func():
    view = resolve("/drinks/delete/1/")

    assert views.Delete is view.func.view_class


def test_view_drinks_delete_200(client_logged):
    p = DrinkFactory()

    url = reverse("drinks:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


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


# -------------------------------------------------------------------------------------
#                                                                  Target Create/Update
# -------------------------------------------------------------------------------------
def test_target_func():
    view = resolve("/drinks/index/target/new/")

    assert views.TargetNew is view.func.view_class


def test_target_update_func():
    view = resolve("/drinks/target/update/1/")

    assert views.TargetUpdate is view.func.view_class


@pytest.mark.parametrize(
    "tab, trigger",
    [
        ("index", "reloadIndex"),
        ("data", "reloadData"),
        ("history", "reloadHistory"),
        ("xxx", "reloadIndex"),
    ],
)
def test_target_get_trigger_name(tab, trigger, rf):
    request = rf.get(reverse("drinks:target_new", kwargs={"tab": tab}))

    view = setup_view(views.TargetNew(), request)
    view.kwargs = {"tab": tab}
    actual = view.get_hx_trigger_django()

    assert actual == trigger


@pytest.mark.parametrize(
    "tab, expect_url",
    [
        ("index", reverse_lazy("drinks:target_new", kwargs={"tab": "index"})),
        ("data", reverse_lazy("drinks:target_new", kwargs={"tab": "data"})),
        ("history", reverse_lazy("drinks:target_new", kwargs={"tab": "history"})),
        ("xxx", reverse_lazy("drinks:target_new", kwargs={"tab": "index"})),
    ],
)
def test_target_new_load_form(client_logged, tab, expect_url):
    url = reverse("drinks:target_new", kwargs={"tab": tab})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert response.status_code == 200

    assert f'hx-post="{expect_url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


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


def test_target_new_invalid_data(client_logged):
    data = {"year": -2, "quantity": "x"}
    url = reverse("drinks:target_new", kwargs={"tab": "index"})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


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
    response = client_logged.get(url)
    form = response.context["form"]

    assert f'name="quantity" value="{expect}"' in form.as_p()


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


# -------------------------------------------------------------------------------------
#                                                                      SelectDrink View
# -------------------------------------------------------------------------------------
def test_select_drink_func():
    view = resolve("/drinks/drink_type/xxx/")
    assert views.SelectDrink == view.func.view_class


def test_select_drink_redirect(client_logged):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})
    response = client_logged.get(url)

    assert response.status_code == 302


def test_select_drink_redirect_follow(client_logged):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"})
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.TabIndex == response.resolver_match.func.view_class


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


def test_select_drink_htmx_stays_on_current_tab(client_logged):
    url = (
        reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"}) + "?tab=trends"
    )
    response = client_logged.get(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert "reloadTrends" in response.headers.get("HX-Trigger", "")
    assert User.objects.first().drink_type == "wine"


def test_select_drink_htmx_unknown_tab_falls_back_to_index(client_logged):
    url = reverse("drinks:set_drink_type", kwargs={"drink_type": "wine"}) + "?tab=xxx"
    response = client_logged.get(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert "reloadIndex" in response.headers.get("HX-Trigger", "")
