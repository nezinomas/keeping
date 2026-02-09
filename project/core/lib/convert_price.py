import calendar


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
    return 0.0 if value is None else value / 100.0


class ConvertToPriceMixin:
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
            # Use getattr with a default of None for safety
            if (val := getattr(obj, field_name, None)) is not None:
                setattr(obj, field_name, int_cents_to_float(val))

        return obj


class PlansConvertToCentsMixin:
    def get_object(self):
        obj = super().get_object()

        months = list(calendar.month_name[1:])
        for month in months:
            if value := getattr(obj, month.lower()):
                setattr(obj, month.lower(), value / 100)
        return obj


class ConvertToCentsMixin:
    price_fields = ["price", "fee"]

    def clean(self):
        cleaned_data = super().clean()
        print(f'--------------------------->\n{cleaned_data=}\n')
        for field_name in self.price_fields:
            if not (val := cleaned_data.get(field_name)):
                continue

            cleaned_data[field_name] = float_to_int_cents(val)

        return cleaned_data
