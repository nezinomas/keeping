from django.db.models import Q

from ...accounts.models import AccountBalance
from ...bookkeeping.lib import helpers as calc
from ...core.signals_base import SignalBase


class AccountBalanceMixin():
    original_price = 0.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.original_price = self.price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.update_accountbalance_table('save')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.update_accountbalance_table('delete')

    def update_accountbalance_table(self, caller: str):
        year = self.date.year

        for _field_name, _account_fk in self.fields.items():
            _pk = getattr(self, _account_fk)

            try:
                _qs = (
                    AccountBalance
                    .objects
                    .get(Q(year=year) & Q(account_id=_pk))
                )

            except AccountBalance.DoesNotExist:
                SignalBase.accounts(sender=type(self), instance=None)
                return

            _field_value = getattr(_qs, _field_name)
            _field_value = self._calc_field(caller, _field_value)

            setattr(_qs, _field_name, _field_value)

            _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
            _qs.delta = calc.calc_delta([_qs.have, _qs.balance])

            _qs.save()

    def _calc_field(self, /, caller, field_value):
        price = float(self.price)
        original_price = float(self.original_price)

        _switch = {
            'save': field_value - original_price + price,
            'delete': field_value - price
        }
        return _switch.get(caller, field_value)
