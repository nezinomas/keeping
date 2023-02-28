import calendar


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
            self.instance.price = int(price * 100)

        if fee := self.cleaned_data.get("fee"):
            self.instance.fee = int(fee * 100)

        return super().save(*args, **kwargs)
