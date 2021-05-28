from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.mixins.from_db import MixinFromDbAccountId
from ..users.models import User
from . import managers


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
    objects = managers.BorrowQuerySet.as_manager()

    def __str__(self):
        return f'Pasiskolinta {round(self.price, 0)}'


