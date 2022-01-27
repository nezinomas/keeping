from django.db import models


# from_db method returns dictionary _old_values
# in case account changed: _old_values={'account_id': [old_account_id, new_account_id]}
# in case account same: _old_values={'account_id': [account_id]}
# _old_values used in signals to find out which accounts to update
class FromDbAccountIdMixin():
    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values):
        zipped = dict(zip(field_names, values))
        instance = super().from_db(db, field_names, values)
        instance._old_values = {
            'account_id': [zipped.get('account_id')]
        }

        return instance
