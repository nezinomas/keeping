from django.db import models


class MixinFromDbAccountId(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values):
        zipped = dict(zip(field_names, values))
        instance = super().from_db(db, field_names, values)
        instance._old_values = [
            zipped.get('account_id')
        ]

        return instance


class MixinFromDbFromAccountId(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values):
        zipped = dict(zip(field_names, values))
        instance = super().from_db(db, field_names, values)
        instance._old_values = [
            zipped.get('to_account_id'),
            zipped.get('from_account_id'),
        ]

        return instance
