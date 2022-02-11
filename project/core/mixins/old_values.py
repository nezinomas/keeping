def _getattr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except AttributeError:
        return default


class OldValuesMixin():
    old_values = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.old_values.update({
                'price': self.price,
                'account': _getattr(self, 'account_id'),
                'saving_type': _getattr(self, 'saving_type_id'),
                'pension_type': _getattr(self, 'pension_type_id'),
                'to_account': _getattr(self, 'to_account_id'),
                'from_account': _getattr(self, 'from_account_id'),
            })

            if _getattr(self, 'fee'):
                self.old_values.update({
                    'fee': self.fee
                })
