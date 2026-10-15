from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ...core.tests.utils import clean_content
from .. import models
from .factories import Pension, PensionFactory, PensionTypeFactory

pytestmark = pytest.mark.django_db


def test_types_list_shows_the_title(client_logged):
    PensionTypeFactory(title="Fondas")

    response = client_logged.get(reverse("pensions:type_list"))

    assert "Fondas" in response.content.decode("utf-8")


@time_machine.travel("2000-03-04")
def test_pensions_load_form(client_logged):
    url = reverse("pensions:new")

    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual
    assert 'name="date" value="1999-03-04"' in actual


def test_pensions_save(client_logged):
    i = PensionTypeFactory()

    data = {"date": "1999-01-01", "price": "0.01", "fee": "0.01", "pension_type": i.pk}

    url = reverse("pensions:new")
    client_logged.post(url, data, follow=True)
    actual = Pension.objects.get()

    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.pension_type.title == "PensionType"


def test_pensions_save_invalid_data(client_logged):
    data = {"date": "x", "price": "x", "pension_type": "x"}

    url = reverse("pensions:new")

    response = client_logged.post(url, data)

    form = response.context["form"]

    assert not form.is_valid()


def test_pensions_load_update_load_form(client_logged):
    obj = PensionFactory()

    url = reverse("pensions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert f'hx-post="{url}"' in actual
    assert "Atnaujinti ir uždaryti</button>" in actual


@pytest.mark.parametrize(
    "price, fee, expected_price, expected_fee",
    [(1, 1, 0.01, 0.01), (1, 0, 0.01, 0), (0, 1, 0, 0.01)],
    ids=["both", "no_fee", "no_price"],
)
def test_pensions_load_update_form_field_values(
    client_logged, price, fee, expected_price, expected_fee
):
    obj = PensionFactory(price=price, fee=fee)

    url = reverse("pensions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == expected_price
    assert form.instance.fee == expected_fee
    assert form.instance.pension_type.title == "PensionType"
    assert form.instance.remark == "remark"


@pytest.mark.parametrize(
    "price, fee, empty, filled",
    [(1, 0, "fee", "price"), (0, 1, "price", "fee")],
    ids=["zero_fee", "zero_price"],
)
def test_pensions_update_form_shows_a_stored_zero_as_empty(
    client_logged, price, fee, empty, filled
):
    obj = PensionFactory(price=price, fee=fee)

    url = reverse("pensions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert f'name="{empty}"' in str(form[empty])
    assert 'value="' not in str(form[empty])
    assert 'value="0.01"' in str(form[filled])


def test_pensions_update_to_another_year(client_logged):
    pension = PensionFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "remark": "Pastaba",
        "pension_type": pension.pension_type.pk,
    }
    url = reverse("pensions:update", kwargs={"pk": pension.pk})

    response = client_logged.post(url, data, follow=True)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


def test_pensions_update(client_logged):
    pension = PensionFactory()

    data = {
        "price": "0.01",
        "fee": "0.01",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "pension_type": pension.pension_type.pk,
    }
    url = reverse("pensions:update", kwargs={"pk": pension.pk})

    response = client_logged.post(url, data, follow=True)

    assert response.status_code == 200

    actual = Pension.objects.get(pk=pension.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.remark == "Pastaba"


def test_pensions_not_load_other_journal(client_logged, second_user):
    it1 = PensionTypeFactory(title="xxx")
    it2 = PensionTypeFactory(title="yyy", journal=second_user.journal)

    PensionFactory(pension_type=it1)
    i2 = PensionFactory(pension_type=it2, price=666)

    url = reverse("pensions:update", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize(
    "price, fee, shown_price, shown_fee",
    [
        (7777, 8888, "77,77", "88,88"),
        (100_000_000, 100_000, "1.000.000,00", "1.000,00"),
    ],
    ids=["converted", "with_thousands"],
)
def test_pensions_list_price_converted(
    client_logged, price, fee, shown_price, shown_fee
):
    PensionFactory(price=price, fee=fee)

    url = reverse("pensions:list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert shown_price in actual
    assert shown_fee in actual


def test_view_pensions_delete_load_form(client_logged):
    p = PensionFactory()

    url = reverse("pensions:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert '<form method="POST"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_view_pensions_delete(client_logged):
    p = PensionFactory()

    assert models.Pension.objects.all().count() == 1
    url = reverse("pensions:delete", kwargs={"pk": p.pk})

    client_logged.post(url, follow=True)

    assert models.Pension.objects.all().count() == 0


def test_pensions_delete_other_journal_get_form(client_logged, second_user):
    it2 = PensionTypeFactory(title="yyy", journal=second_user.journal)
    i2 = PensionFactory(pension_type=it2, price=666)

    url = reverse("pensions:delete", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_pensions_delete_other_journal_post_form(client_logged, second_user):
    it2 = PensionTypeFactory(title="yyy", journal=second_user.journal)
    i2 = PensionFactory(pension_type=it2, price=666)

    url = reverse("pensions:delete", kwargs={"pk": i2.pk})
    client_logged.post(url)

    assert Pension.objects.all().count() == 1


def test_type_save(client_logged):
    data = {"title": "TTT"}
    url = reverse("pensions:type_new")

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_type_new_load_form(client_logged):
    url = reverse("pensions:type_new")

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_type_save_invalid_data(client_logged):
    data = {"title": ""}

    url = reverse("pensions:type_new")

    response = client_logged.post(url, data, follow=True)

    form = response.context["form"]

    assert not form.is_valid()


def test_type_update_load_form(client_logged):
    pension = PensionTypeFactory()

    url = reverse("pensions:type_update", kwargs={"pk": pension.pk})

    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_type_update(client_logged):
    pension = PensionTypeFactory()

    data = {"title": "TTT"}
    url = reverse("pensions:type_update", kwargs={"pk": pension.pk})

    response = client_logged.post(url, data, follow=True)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_pension_type_not_load_other_journal(client_logged, second_user):
    PensionTypeFactory(title="xxx")
    obj = PensionTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("pensions:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404
