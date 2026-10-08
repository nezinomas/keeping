import pytest
import time_machine
from django.urls import reverse

from ....core.tests.utils import setup_view
from ....savings.models import SavingBalance
from ....savings.tests.factories import SavingTypeFactory
from ... import views
from ...models import SavingWorth

pytestmark = pytest.mark.django_db


def test_formset_load(client_logged):
    SavingTypeFactory()

    url = reverse("bookkeeping:savings_worth_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Fondų vertė" in actual
    assert '<option value="1" selected>Savings</option>' in actual


@time_machine.travel("1999-2-3")
@pytest.mark.parametrize(
    "price, expected",
    [
        pytest.param("0.01", 1, id="new"),
        pytest.param("0", 0, id="null_value"),
    ],
)
def test_formset_new(price, expected, client_logged):
    i = SavingTypeFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-2-3",
        "form-0-price": price,
        "form-0-saving_type": i.pk,
    }

    url = reverse("bookkeeping:savings_worth_new")
    client_logged.post(url, data)

    actual = SavingWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 2
    assert actual.date.day == 3
    assert actual.price == expected


def test_formset_new_post_save(client_logged):
    i = SavingTypeFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-2-3",
        "form-0-price": "0.01",
        "form-0-saving_type": i.pk,
    }

    url = reverse("bookkeeping:savings_worth_new")
    client_logged.post(url, data)

    actual = SavingBalance.objects.get(year=1999)
    assert actual.market_value == 1


def test_formset_invalid_data(client_logged):
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-1-32",
        "form-0-price": "x",
        "form-0-saving_type": 0,
    }

    url = reverse("bookkeeping:savings_worth_new")
    response = client_logged.post(url, data)
    form = response.context["formset"]

    assert not form.is_valid()


@pytest.mark.parametrize(
    "year, listed",
    [
        pytest.param(2000, False, id="past"),
        pytest.param(1000, True, id="current"),
        pytest.param(1, True, id="future"),
    ],
)
def test_formset_lists_a_saving_type_until_its_closing_year(
    year, listed, main_user, rf
):
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)

    main_user.year = year
    rf.user = main_user

    view = setup_view(views.SavingsWorthNew(), rf)

    actual = str(view.get_formset())

    assert "S1" in actual
    assert ("S2" in actual) is listed
