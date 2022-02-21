from ..lib import utils


class OldValuesMixin():
    old_values = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.old_values.update({
                'price': self.price,
                'account': utils._getattr(self, 'account_id'),
                'saving_type': utils._getattr(self, 'saving_type_id'),
                'pension_type': utils._getattr(self, 'pension_type_id'),
                'to_account': utils._getattr(self, 'to_account_id'),
                'from_account': utils._getattr(self, 'from_account_id'),
            })

            if utils._getattr(self, 'fee'):
                self.old_values.update({
                    'fee': self.fee
                })
