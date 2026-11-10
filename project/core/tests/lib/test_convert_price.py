from types import SimpleNamespace

import pytest
from django import forms
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.convert_price import (
    PriceNeverEmptyFormMixin,
    PriceToCentsFormMixin,
    PriceToFloatViewMixin,
    float_to_int_cents,
    int_cents_to_float,
)


@st.composite
def prices_and_cents(draw):
    """A price written with a third decimal digit, and the cents it truncates to."""
    cents = draw(st.integers(0, 10**9))
    past_the_cent = draw(st.sampled_from("0123456789"))
    whole, part = divmod(cents, 100)

    return float(f"{whole}.{part:02d}{past_the_cent}"), cents


@given(prices_and_cents())
@example((0.01, 1))
@example((4669.73, 466973))  # 4669.73 * 100 is 466972.99999999994 in binary
@example((4669.736, 466973))
@example((466.73, 46673))
@example((0.0, 0))
@example((0.019, 1))
def test_float_to_int_cents_drops_the_digits_past_the_cent(case):
    price, cents = case

    assert float_to_int_cents(price) == cents


@pytest.mark.parametrize("convert", [float_to_int_cents, int_cents_to_float])
def test_conversions_take_a_number_only(convert):
    with pytest.raises(TypeError):
        convert(None)


@pytest.mark.parametrize(
    "cents_int, expected_float",
    [
        (1, 0.01),
        (466973, 4669.73),
        (46673, 466.73),
        (0, 0.0),
        (100, 1.0),
    ],
)
def test_int_cents_to_float_conversion(cents_int, expected_float):
    assert int_cents_to_float(cents_int) == expected_float


class DummyBase:
    def get_object(self):
        pass

    def get_form_class(self):
        return self.form_class


class Cleaned:
    """A form base whose `clean` hands back the data it was built with."""

    def __init__(self, data):
        self.data = data

    def clean(self):
        return self.data


def _view(mocker, obj, fields=("price", "fee")):
    mocker.patch.object(DummyBase, "get_object", return_value=obj)

    class DummyForm:
        price_fields = fields

    class DummyView(PriceToFloatViewMixin, DummyBase):
        form_class = DummyForm

    return DummyView()


def _form(data, fields=("price", "fee")):
    class DummyForm(PriceToCentsFormMixin, Cleaned):
        price_fields = fields

    return DummyForm(data)


@pytest.mark.parametrize(
    "cents, expected_float",
    [
        (466973, 4669.73),
        (100, 1.0),
        (0, 0),
    ],
)
def test_view_mixin_converts_declared_fields(mocker, cents, expected_float):
    result = _view(mocker, SimpleNamespace(price=cents, fee=cents)).get_object()

    assert result.price == expected_float
    assert result.fee == expected_float


@pytest.mark.parametrize(
    "obj, fields, expect",
    [
        pytest.param(
            {"price": 1000, "fee": 2000},
            ("price",),
            {"price": 10.0, "fee": 2000},
            id="only_declared_fields",
        ),
        pytest.param(
            {"price": 1000, "fee": 2000, "new_field": 3000},
            ("new_field",),
            {"price": 1000, "fee": 2000, "new_field": 30.0},
            id="any_declared_name",
        ),
    ],
)
def test_view_mixin_converts_only_the_declared_fields(mocker, obj, fields, expect):
    result = _view(mocker, SimpleNamespace(**obj), fields).get_object()

    assert vars(result) == expect


def test_view_mixin_raises_for_a_declared_field_the_object_lacks(mocker):
    view = _view(mocker, SimpleNamespace(price=1000), ("price", "fee"))

    with pytest.raises(AttributeError):
        view.get_object()


def test_view_mixin_without_price_fields_on_the_form_raises(mocker):
    mocker.patch.object(DummyBase, "get_object", return_value=SimpleNamespace())

    class DummyForm:
        pass

    class DummyView(PriceToFloatViewMixin, DummyBase):
        form_class = DummyForm

    with pytest.raises(AttributeError):
        DummyView().get_object()


@given(prices_and_cents())
@example((0.01, 1))
@example((4669.73, 466973))
@example((4669.736, 466973))
@example((466.73, 46673))
@example((0.0, 0))
@example((0.019, 1))
@example((None, None))
def test_form_mixin_converts_declared_fields(case):
    price, cents = case

    result = _form({"price": price, "fee": price}).clean()

    assert (result["price"], result["fee"]) == (cents, cents)


@pytest.mark.parametrize(
    "data, fields, expect",
    [
        pytest.param(
            {"price": 1, "fee": 2},
            ("price",),
            {"price": 100, "fee": 2},
            id="only_declared_fields",
        ),
        pytest.param(
            {"price": 1, "new_field": 3},
            ("new_field",),
            {"price": 1, "new_field": 300},
            id="any_declared_name",
        ),
    ],
)
def test_form_mixin_converts_only_the_declared_fields(data, fields, expect):
    assert _form(data, fields).clean() == expect


def test_form_mixin_skips_a_declared_field_that_is_absent():
    result = _form({"price": 1}).clean()

    assert result == {"price": 100}


def test_form_mixin_without_price_fields_raises():
    class DummyForm(PriceToCentsFormMixin, Cleaned):
        pass

    with pytest.raises(AttributeError):
        DummyForm({"price": 1}).clean()


class _PriceForm(PriceNeverEmptyFormMixin, forms.Form):
    price = forms.IntegerField(required=False)
    fee = forms.IntegerField(required=False)


@pytest.mark.parametrize("empty", ["", None])
def test_price_never_empty_saves_an_empty_field_as_zero(empty):
    form = _PriceForm(data={"price": empty, "fee": 5})

    assert form.is_valid()
    assert form.cleaned_data == {"price": 0, "fee": 5}


def test_price_never_empty_shows_a_stored_zero_as_empty():
    form = _PriceForm(initial={"price": 0, "fee": 7})

    assert form["price"].value() == ""
    assert form["fee"].value() == 7


def test_price_never_empty_shows_a_missing_value_as_empty():
    form = _PriceForm()

    assert form["price"].value() == ""
    assert form["fee"].value() == ""


@pytest.mark.parametrize("price, fee", [("", ""), (None, None), (0, 0), ("", 0)])
def test_price_never_empty_rejects_both_empty(price, fee):
    form = _PriceForm(data={"price": price, "fee": fee})

    assert not form.is_valid()
    assert set(form.errors) == {"price", "fee"}


def test_price_never_empty_accepts_one_of_the_two():
    assert _PriceForm(data={"price": "", "fee": 1}).is_valid()
    assert _PriceForm(data={"price": 1, "fee": ""}).is_valid()
