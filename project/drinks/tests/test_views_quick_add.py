from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ...users.tests.factories import User
from .. import models
from .factories import DrinkFactory

pytestmark = pytest.mark.django_db


def test_quick_add_url_reverses():
    url = reverse("drinks:quick_add")
    assert url == "/drinks/quick_add/"


def test_quick_add_post_creates_drink(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert models.Drink.objects.count() == 1

    drink = models.Drink.objects.last()
    assert drink.option == "beer"
    # 2.5 units of beer = 2.5 / 0.4 stdav = 6.25 stdav (based on beer ratio of 0.4)
    assert drink.stdav == pytest.approx(6.25, rel=0.01)


def test_quick_add_post_omits_option_uses_user_drink_type(client_logged, main_user):
    main_user.drink_type = "wine"
    main_user.save()

    data = {
        "quantity": 8,
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    drink = models.Drink.objects.last()
    assert drink.option == "wine"


@pytest.mark.parametrize(
    "tab, trigger",
    [
        ("index", "reloadIndex"),
        ("data", "reloadData"),
        ("history", "reloadHistory"),
        ("trends", "reloadTrends"),
        ("risk", "reloadRisk"),
        ("habits", "reloadHabits"),
        # an unrecognised tab lands on Overview
        ("unknown", "reloadIndex"),
    ],
)
def test_quick_add_post_reloads_the_tab_it_was_fired_from(tab, trigger, client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": tab,
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert trigger in response.headers.get("HX-Trigger", "")


@pytest.mark.parametrize("quantity", [None, "", "invalid"])
def test_quick_add_post_unusable_quantity_returns_422(quantity, client_logged):
    data = {
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    if quantity is not None:
        data["quantity"] = quantity

    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 422
    assert models.Drink.objects.count() == 0


def test_quick_add_get_returns_405(client_logged):
    url = reverse("drinks:quick_add")
    response = client_logged.get(url)

    assert response.status_code == 405


def test_quick_add_post_omits_date_uses_set_date_with_user_year(
    client_logged, main_user
):
    with time_machine.travel("1999-01-15"):
        data = {
            "quantity": 2.5,
            "option": "beer",
            "tab": "index",
        }
        url = reverse("drinks:quick_add")
        response = client_logged.post(url, data)

        assert response.status_code == 204
        drink = models.Drink.objects.last()
        # set_date_with_user_year should default to today when viewing current year
        assert drink.date.year == 1999


def quantity_input(html):
    """The quick-add quantity tag on its own, so attributes can be asserted."""
    start = html.index('<input type="text" name="quantity"')

    return html[start : html.index(">", start) + 1]


def test_quick_add_quantity_input_is_a_text_field(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)
    html = response.content.decode("utf-8")

    assert 'inputmode="decimal"' in quantity_input(html)


def test_quick_add_quantity_rewrites_a_decimal_comma_on_the_model(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)
    html = response.content.decode("utf-8")

    assert "quantity.replace(',', '.')" in quantity_input(html)


def test_quick_add_quantity_drops_what_is_not_a_number(client_logged):
    # 150b answered 422 with an empty body, so the sheet said nothing at all —
    # and a second dot is no more parseable than a letter
    url = reverse("drinks:index")
    response = client_logged.get(url)
    tag = quantity_input(response.content.decode("utf-8"))

    assert "[^0-9.]" in tag
    assert r"^(\d*\.?\d*).*" in tag


def test_quick_add_quantity_arrows_step_by_drink_type(client_logged):
    # a text field has no native spinner, so the steps are drawn and driven here
    url = reverse("drinks:index")
    response = client_logged.get(url)
    html = response.content.decode("utf-8")

    assert "steps: { beer: 1, wine: 50, vodka: 10, stdav: 1 }" in html
    assert 'class="quick-add__spin-up"' in html
    assert 'class="quick-add__spin-down"' in html
    assert '@click="step(1)"' in html
    assert '@click="step(-1)"' in html


def test_quick_add_quantity_steps_from_the_keyboard(client_logged):
    # a native spin button is not focusable either; the arrow keys are the path
    url = reverse("drinks:index")
    response = client_logged.get(url)
    tag = quantity_input(response.content.decode("utf-8"))

    assert '@keydown.up.prevent="step(1)"' in tag
    assert '@keydown.down.prevent="step(-1)"' in tag


def test_quick_add_fields_run_day_then_drink_type_then_quantity(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)
    html = response.content.decode("utf-8")

    day = html.index('class="select-wrapper quick-add__day"')
    drink_type = html.index('class="select-wrapper quick-add__type"')
    quantity = html.index('class="form-control quick-add__qty"')

    assert day < drink_type < quantity


def test_quick_add_has_a_day_select(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)
    html = response.content.decode("utf-8")

    assert 'class="select-wrapper quick-add__day"' in html
    assert '<select name="date" class="form-select"' in html


def test_quick_add_day_select_offers_today_and_the_four_days_before_it(client_logged):
    with time_machine.travel("1999-01-15"):
        url = reverse("drinks:index")
        response = client_logged.get(url)
        html = response.content.decode("utf-8")

    assert '<option value="1999-01-15" selected>Šiandien</option>' in html
    assert '<option value="1999-01-14">Vakar</option>' in html
    assert '<option value="1999-01-13">Trečiadienis</option>' in html
    assert '<option value="1999-01-12">Antradienis</option>' in html
    assert '<option value="1999-01-11">Pirmadienis</option>' in html


def test_quick_add_day_select_uses_today_not_the_year_being_browsed(
    client_logged, main_user
):
    main_user.year = 1998
    main_user.save()

    with time_machine.travel("1999-01-15"):
        url = reverse("drinks:index")
        response = client_logged.get(url)
        html = response.content.decode("utf-8")

    assert '<option value="1999-01-15" selected>Šiandien</option>' in html


def test_index_context_has_recent_days(client_logged):
    with time_machine.travel("1999-01-15"):
        url = reverse("drinks:index")
        response = client_logged.get(url)

    assert response.context["recent_days"].selected == "1999-01-15"


def test_quick_add_post_stores_the_chosen_day(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-13",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert models.Drink.objects.last().date == date(1999, 1, 13)
