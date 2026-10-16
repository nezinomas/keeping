import pytest
from django.urls import reverse

from ....pensions.models import PensionBalance
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ...models import PensionWorth

pytestmark = pytest.mark.django_db


def test_formset_load(client_logged):
    PensionFactory()

    url = reverse("bookkeeping:pensions_worth_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Pensijų vertė" in actual
    assert '<option value="1" selected>PensionType</option>' in actual


@pytest.mark.parametrize(
    "price, expected",
    [
        pytest.param("0.01", 1, id="new"),
        pytest.param("0", 0, id="null_value"),
    ],
)
def test_formset_new(client_logged, price, expected):
    i = PensionTypeFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-2-3",
        "form-0-price": price,
        "form-0-pension_type": i.pk,
    }

    url = reverse("bookkeeping:pensions_worth_new")
    client_logged.post(url, data)

    actual = PensionWorth.objects.last()
    assert actual.date.year == 1999
    assert actual.date.month == 2
    assert actual.date.day == 3
    assert actual.price == expected


def test_formset_new_post_save(client_logged):
    i = PensionTypeFactory()
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "1999-2-3",
        "form-0-price": "0.01",
        "form-0-pension_type": i.pk,
    }

    url = reverse("bookkeeping:pensions_worth_new")
    client_logged.post(url, data)

    actual = PensionBalance.objects.get(year=1999)
    assert actual.market_value == 1


def test_formset_invalid_data(client_logged):
    data = {
        "form-TOTAL_FORMS": 1,
        "form-INITIAL_FORMS": 0,
        "form-0-date": "x",
        "form-0-price": "x",
        "form-0-pension_type": 0,
    }

    url = reverse("bookkeeping:pensions_worth_new")
    response = client_logged.post(url, data)
    form = response.context["formset"]

    assert not form.is_valid()
    assert "date" in form.errors[0]
    assert "price" in form.errors[0]
    assert "pension_type" in form.errors[0]
