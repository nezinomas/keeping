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
    initial_count = models.Drink.objects.count()

    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert models.Drink.objects.count() == initial_count + 1


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


def test_quick_add_post_successful_returns_204_with_hx_trigger_index(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert "reloadIndex" in response.headers.get("HX-Trigger", "")


def test_quick_add_post_successful_returns_204_with_hx_trigger_data(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "data",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert "reloadData" in response.headers.get("HX-Trigger", "")


def test_quick_add_post_successful_returns_204_with_hx_trigger_history(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "history",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert "reloadHistory" in response.headers.get("HX-Trigger", "")


def test_quick_add_post_successful_returns_204_with_hx_trigger_trends(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "trends",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert "reloadTrends" in response.headers.get("HX-Trigger", "")


def test_quick_add_post_successful_returns_204_with_hx_trigger_risk(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "risk",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert "reloadRisk" in response.headers.get("HX-Trigger", "")


def test_quick_add_post_unknown_tab_falls_back_to_index(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "unknown",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    assert "reloadIndex" in response.headers.get("HX-Trigger", "")


def test_quick_add_post_missing_quantity_returns_422(client_logged):
    initial_count = models.Drink.objects.count()

    data = {
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 422
    assert models.Drink.objects.count() == initial_count


def test_quick_add_post_empty_quantity_returns_422(client_logged):
    initial_count = models.Drink.objects.count()

    data = {
        "quantity": "",
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 422
    assert models.Drink.objects.count() == initial_count


def test_quick_add_post_invalid_quantity_returns_422(client_logged):
    initial_count = models.Drink.objects.count()

    data = {
        "quantity": "invalid",
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 422
    assert models.Drink.objects.count() == initial_count


def test_quick_add_get_returns_405(client_logged):
    url = reverse("drinks:quick_add")
    response = client_logged.get(url)

    assert response.status_code == 405


def test_quick_add_stores_expected_stdav(client_logged):
    data = {
        "quantity": 2.5,
        "option": "beer",
        "date": "1999-01-01",
        "tab": "index",
    }
    url = reverse("drinks:quick_add")
    response = client_logged.post(url, data)

    assert response.status_code == 204
    drink = models.Drink.objects.last()
    assert drink.option == "beer"
    # 2.5 units of beer = 2.5 / 0.4 stdav = 6.25 stdav (based on beer ratio of 0.4)
    assert drink.stdav == pytest.approx(6.25, rel=0.01)


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


def test_quick_add_quantity_input_has_form_control_class(client_logged):
    url = reverse("drinks:index")
    response = client_logged.get(url)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert 'class="form-control quick-add__qty"' in html


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
