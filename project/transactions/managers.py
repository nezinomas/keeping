from django.db import models

from ..core.mixins.sum import SumMixin
from ..users.models import User


class BaseMixin(models.QuerySet):
    def related(self, user: User):
        return self.select_related("from_account", "to_account").filter(
            from_account__journal=user.journal, to_account__journal=user.journal
        )


class TransactionQuerySet(BaseMixin):
    pass


class SavingCloseQuerySet(BaseMixin, SumMixin):
    pass


class SavingChangeQuerySet(BaseMixin):
    pass
