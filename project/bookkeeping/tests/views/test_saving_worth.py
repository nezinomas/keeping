import pytest
import time_machine
from django.urls import resolve, reverse

from ....core.tests.utils import setup_view
from ....savings.models import SavingBalance
from ....savings.tests.factories import SavingTypeFactory
from ...models import SavingWorth
from ... import views

pytestmark = pytest.mark.django_db


def test_view_func():
    view = resolve("/bookkeeping/savings_worth/new/")

    assert views.SavingsWorthNew == view.func.view_class


def test_view_200(client_logged):
    url = reverse("bookkeeping:savings_worth_new")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_formset_load(client_logged):
    SavingTypeFactory()

    url = reverse("bookkeeping:savings_worth_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "Fondų vertė" in actual
    assert '<option value="1" selected>Savings</option>' in actual


@time_machine.travel("1999-2-3")
def test_formset_new(client_logged):
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

    actual = SavingWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 2
    assert actual.date.day == 3
    assert actual.price == 1


@time_machine.travel("1999-2-3")
def test_formset_new_null_value(client_logged):
    i = SavingTypeFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-2-3",
        "form-0-price": "0",
        "form-0-saving_type": i.pk,
    }

    url = reverse("bookkeeping:savings_worth_new")
    client_logged.post(url, data)

    actual = SavingWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 2
    assert actual.date.day == 3
    assert not actual.price


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


def test_formset_saving_type_closed_in_past(main_user, rf):
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)

    main_user.year = 2000
    rf.user = main_user

    view = setup_view(views.SavingsWorthNew(), rf)

    actual = str(view.get_formset())  # pylint: disable=protected-access

    assert "S1" in actual
    assert "S2" not in actual


def test_formset_saving_type_closed_in_current(main_user, rf):
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)

    main_user.year = 1000
    rf.user = main_user

    view = setup_view(views.SavingsWorthNew(), rf)

    actual = str(view.get_formset())  # pylint: disable=protected-access

    assert "S1" in actual
    assert "S2" in actual


def test_formset_saving_type_closed_in_future(main_user, rf):
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)

    main_user.year = 1
    rf.user = main_user

    view = setup_view(views.SavingsWorthNew(), rf)

    actual = str(view.get_formset())  # pylint: disable=protected-access

    assert "S1" in actual
    assert "S2" in actual
