from types import SimpleNamespace

import pytest
from django import forms

from ...lib.convert_price import (
    PriceNeverEmptyFormMixin,
    PriceToCentsFormMixin,
    PriceToFloatViewMixin,
    float_to_int_cents,
    int_cents_to_float,
)


@pytest.mark.parametrize(
    "price_float, expected_int",
    [
        (0.01, 1),  # Standard case
        (4669.73, 466973),  # Scenario 1: Exact two decimals
        (4669.736, 466973),  # Scenario 2: Truncation (discarding .006)
        (466.73, 46673),  # Known binary noise case
        (0.0, 0),  # Zero case
        (0.019, 1),  # Truncation verification
    ],
)
def test_float_to_int_conversion(price_float, expected_int):
    assert float_to_int_cents(price_float) == expected_int


def test_float_to_int_cents_takes_a_number_only():
    with pytest.raises(TypeError):
        float_to_int_cents(None)


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


def test_int_cents_to_float_takes_an_int_only():
    with pytest.raises(TypeError):
        int_cents_to_float(None)


class DummyBase:
    def get_object(self):
        pass

    def get_form_class(self):
        return self.form_class

    def clean(self):
        pass


def _view(mocker, obj, fields=("price", "fee")):
    mocker.patch.object(DummyBase, "get_object", return_value=obj)

    class DummyForm:
        price_fields = fields

    class DummyView(PriceToFloatViewMixin, DummyBase):
        form_class = DummyForm

    return DummyView()


def _form(mocker, data, fields=("price", "fee")):
    mocker.patch.object(DummyBase, "clean", return_value=data)

    class DummyForm(PriceToCentsFormMixin, DummyBase):
        price_fields = fields

    return DummyForm()


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


def test_view_mixin_reads_price_fields_from_the_form_class(mocker):
    mocker.patch.object(
        DummyBase, "get_object", return_value=SimpleNamespace(price=1000)
    )

    class DummyForm:
        price_fields = ("price",)

    class DummyView(PriceToFloatViewMixin, DummyBase):
        form_class = DummyForm

    assert DummyView().get_object().price == 10.0


def test_view_mixin_without_price_fields_on_the_form_raises(mocker):
    mocker.patch.object(DummyBase, "get_object", return_value=SimpleNamespace())

    class DummyForm:
        pass

    class DummyView(PriceToFloatViewMixin, DummyBase):
        form_class = DummyForm

    with pytest.raises(AttributeError):
        DummyView().get_object()


@pytest.mark.parametrize(
    "price, expected_int",
    [
        (0.01, 1),  # Standard case
        (4669.73, 466973),  # Scenario 1: Exact two decimals
        (4669.736, 466973),  # Scenario 2: Truncation (discarding .006)
        (466.73, 46673),  # Known binary noise case
        (0.0, 0),  # Zero case
        (0.019, 1),  # Truncation verification
        (None, None),
    ],
)
def test_form_mixin_converts_declared_fields(mocker, price, expected_int):
    result = _form(mocker, {"price": price, "fee": price}).clean()

    assert result["price"] == expected_int
    assert result["fee"] == expected_int


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
def test_form_mixin_converts_only_the_declared_fields(mocker, data, fields, expect):
    assert _form(mocker, data, fields).clean() == expect


def test_form_mixin_skips_a_declared_field_that_is_absent(mocker):
    result = _form(mocker, {"price": 1}).clean()

    assert result == {"price": 100}


def test_form_mixin_without_price_fields_raises(mocker):
    mocker.patch.object(DummyBase, "clean", return_value={"price": 1})

    class DummyForm(PriceToCentsFormMixin, DummyBase):
        pass

    with pytest.raises(AttributeError):
        DummyForm().clean()


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
