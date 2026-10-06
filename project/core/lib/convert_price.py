import calendar

from django.utils.translation import gettext as _


def float_to_int_cents(value: float) -> int:
    """
    Converts float to integer cents, discarding digits beyond two decimal places.
    Handles IEEE 754 precision issues using epsilon nudging.
    """
    if value is None:
        return 0
    # Multiply by 100 and add epsilon to bridge binary noise
    # Then cast to int to truncate (discard) remaining decimals
    return int(value * 100 + 0.00001)


def int_cents_to_float(value: int) -> float:
    return value / 100


class ConvertPriceMixin:
    # Core defaults that should always be processed
    _base_price_fields = ["price", "fee"]

    # Subclasses define additional fields here
    price_fields = []

    def get_all_price_fields(self):
        """Merges base fields with subclass-specific fields."""
        return set(self._base_price_fields + getattr(self, "price_fields", []))

    def get_object(self):
        obj = super().get_object()

        for field_name in self.get_all_price_fields():
            if (val := getattr(obj, field_name, None)) is not None:
                setattr(obj, field_name, int_cents_to_float(val))

        return obj

    def clean(self):
        cleaned_data = super().clean()

        for field_name in self.get_all_price_fields():
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


class PlanConvertPriceMixin(ConvertPriceMixin):
    def get_all_price_fields(self):
        return [month.lower() for month in calendar.month_name[1:]]
