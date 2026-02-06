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


class ConvertToCents:
    def get_object(self):
        obj = super().get_object()

        if hasattr(obj, "price") and obj.price:
            obj.price = int_cents_to_float(obj.price)

        if hasattr(obj, "fee") and obj.fee:
            obj.fee = int_cents_to_float(obj.fee)

        return obj


class PlansConvertToCents:
    def get_object(self):
        obj = super().get_object()

        months = list(calendar.month_name[1:])
        for month in months:
            if value := getattr(obj, month.lower()):
                setattr(obj, month.lower(), value / 100)
        return obj


class ConvertToPriceMixin:
    def clean_price(self):
        return self._convert_field("price")

    def clean_fee(self):
        return self._convert_field("fee")

    def _convert_field(self, name):
        val = self.cleaned_data.get(name)
        val_cents = float_to_int_cents(val) if val is not None else val
        self.cleaned_data[name] = val_cents
        return val_cents