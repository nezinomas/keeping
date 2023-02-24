import calendar

class ConvertToCents:
    def get_object(self):
        obj = super().get_object()

        if hasattr(obj, 'price') and obj.price:
            obj.price = obj.price / 100

        if hasattr(obj, 'fee') and obj.fee:
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
