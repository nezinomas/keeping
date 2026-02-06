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


class ConvertToCents:
    def get_object(self):
        obj = super().get_object()

        if hasattr(obj, "price") and obj.price:
            obj.price = obj.price / 100

        if hasattr(obj, "fee") and obj.fee:
            obj.fee = obj.fee / 100

        return obj


class PlansConvertToCents:
    def get_object(self):
        obj = super().get_object()

        months = list(calendar.month_name[1:])
        for month in months:
            if value := getattr(obj, month.lower()):
                setattr(obj, month.lower(), value / 100)
        return obj


class ConvertToPrice:
    def save(self, *args, **kwargs):
        if price := self.cleaned_data.get("price"):
            self.instance.price = round(price * 100)

        if fee := self.cleaned_data.get("fee"):
            self.instance.fee = round(fee * 100)

        return super().save(*args, **kwargs)
