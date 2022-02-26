from ..lib import utils


class OldValuesMixin():
    old_values = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.old_values.update({
                'price': self.price,
                'account': utils.getattr_(self, 'account_id'),
                'saving_type': utils.getattr_(self, 'saving_type_id'),
                'pension_type': utils.getattr_(self, 'pension_type_id'),
                'to_account': utils.getattr_(self, 'to_account_id'),
                'from_account': utils.getattr_(self, 'from_account_id'),
            })

            if utils.getattr_(self, 'fee'):
                self.old_values.update({
                    'fee': self.fee
                })
