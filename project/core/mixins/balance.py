from decimal import Decimal

from django.db.models import Q

from ...accounts.models import AccountBalance
from ...bookkeeping.lib import helpers as calc
from ...core.signals import SignalBase


class AccountBalanceMixin():
    def __init__(self,
                 sender: object,
                 caller: str,
                 field_name: str,
                 year: int,
                 account_pk: int,
                 price: Decimal,
                 original_price: Decimal  = 0.0):

        price = float(price)
        original_price = float(original_price)

        try:
            _qs = (
                AccountBalance
                .objects
                .get(Q(year=year) & Q(account_id=account_pk))
            )

            _field = getattr(_qs, field_name)

            if caller == 'save':
                _field = _field - original_price + price

            if caller == 'delete':
                _field = _field - price

            setattr(_qs, field_name, _field)

            _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
            _qs.delta = calc.calc_delta([_qs.have, _qs.balance])

            _qs.save()

        except AccountBalance.DoesNotExist:
            SignalBase.accounts(sender=sender, instance=None)
