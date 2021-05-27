from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..accounts.models import Account
from ..core.lib import utils
from ..core.mixins.from_db import MixinFromDbAccountId
from ..users.models import User


class BorrowQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
            .filter(closed=False)
        )

    def items(self):
        return self.related()

    def year(self, year):
        return self.related().filter(date__year=year)

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'borrow_past': Decimal(),
                'borrow_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('name'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                borrow_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                borrow_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'borrow_past',
                'borrow_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )


class Borrow(MixinFromDbAccountId):
    date = models.DateField()
    name = models.TextField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    returned = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    closed = models.BooleanField(
        default=False
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='borrow_to'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # objects = BookManager()
    objects = BorrowQuerySet.as_manager()

    def __str__(self):
        return f'Pasiskolinta {round(self.price, 0)}'
