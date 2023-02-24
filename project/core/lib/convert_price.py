

class ConvertToCents:
    def get_object(self):
        obj = super().get_object()

        if hasattr(obj, 'price') and obj.price:
            obj.price = obj.price / 100

        if hasattr(obj, 'fee') and obj.fee:
            obj.fee = obj.fee / 100

        return obj
