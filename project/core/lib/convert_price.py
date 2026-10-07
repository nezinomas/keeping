from django.utils.translation import gettext as _


def float_to_int_cents(value: float) -> int:
    """
    Converts float to integer cents, discarding digits beyond two decimal places.
    Handles IEEE 754 precision issues using epsilon nudging.
    """
    # Multiply by 100 and add epsilon to bridge binary noise
    # Then cast to int to truncate (discard) remaining decimals
    return int(value * 100 + 0.00001)


def int_cents_to_float(value: int) -> float:
    return value / 100


class PriceToFloatViewMixin:
    """Edit views: stored cents become the float the form shows. The fields are the
    form's own `price_fields`, so a form that forgets them raises."""

    def get_object(self):
        obj = super().get_object()

        for field_name in self.get_form_class().price_fields:
            setattr(obj, field_name, int_cents_to_float(getattr(obj, field_name)))

        return obj


class PriceToCentsFormMixin:
    """Forms: a posted float becomes cents. `price_fields` is declared by each form,
    with no default, so a form that forgets it raises."""

    def clean(self):
        cleaned_data = super().clean()

        for field_name in self.price_fields:
            if not (val := cleaned_data.get(field_name)):
                continue

            cleaned_data[field_name] = float_to_int_cents(val)

        return cleaned_data


class NeverEmptyFormMixin:
    """NOT NULL columns named in `_never_empty`: an empty field saves 0, and a stored
    0 is shown as an empty field, since the user reads it as nothing entered."""

    _never_empty: tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name in self._never_empty:
            self.initial[name] = self.initial.get(name) or ""

    def clean(self):
        cleaned_data = super().clean()
        self._reject_empty(cleaned_data)

        for name in self._never_empty:
            cleaned_data[name] = cleaned_data.get(name) or 0

        return cleaned_data

    def _reject_empty(self, cleaned_data: dict) -> None:
        return


class PriceNeverEmptyFormMixin(NeverEmptyFormMixin):
    """Price and fee never empty, and not both empty at once."""

    _never_empty = ("price", "fee")

    def _reject_empty(self, cleaned_data: dict) -> None:
        if any(cleaned_data.get(name) for name in self._never_empty):
            return

        _msg = _("The `Sum` and `Fee` fields cannot both be empty.")
        for name in self._never_empty:
            self.add_error(name, _msg)
