from django.db.models import Q

from ...accounts.models import AccountBalance
from ...bookkeeping.lib import helpers as calc
from ...core.signals_base import SignalBase


def _getattr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except AttributeError:
        return default


class AccountBalanceMixin():
    original_price = 0.0
    old_values = {}

    # {model_name: {accountbalce_table_field: model_field}}
    hooks = {
        'Income': {'incomes': 'account'},
        'Expense': {'expenses': 'account'},
        'Lent': {'incomes': 'account'},
        'LentReturn': {'expenses': 'account'},
        'Borrow': {'expenses': 'account'},
        'BorrowReturn': {'incomes': 'account'},
        'Transaction': {
            'incomes': 'to_account',
            'expenses': 'from_account'},
        'AccountWorth': {'have': 'account'}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.original_price = self.price

            self.old_values.update({
                'account': _getattr(self, 'account_id', None),
                'to_account': _getattr(self, 'to_account_id', None),
                'from_account': _getattr(self, 'from_account_id', None),
            })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.update_accountbalance_table('update')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self.update_accountbalance_table()

    def update_accountbalance_table(self, caller: str = None):
        _hook = self.hooks.get(type(self).__name__)

        for _balance_tbl_field_name, _account_name in _hook.items():
            _account = getattr(self, _account_name)
            _old_account_id = self.old_values.get(_account_name)

            if not _old_account_id or _old_account_id == _account.pk:
                try:
                    caller = caller if caller else 'delete'
                    self._update_balance_tbl(caller, _balance_tbl_field_name, _account.pk)
                except AccountBalance.DoesNotExist:
                    return
            else:
                try:
                    self._update_balance_tbl('new', _balance_tbl_field_name ,_account.pk)
                    self._update_balance_tbl('delete', _balance_tbl_field_name, _old_account_id)
                except AccountBalance.DoesNotExist:
                    return

    def _calc_field(self, /, caller, field_value):
        price = float(self.price)
        original_price = float(self.original_price)

        _switch = {
            'update': field_value - original_price + price,
            'new': field_value + price,
            'delete': field_value - original_price
        }
        return _switch.get(caller, field_value)

    def _update_balance_tbl(self, caller, balance_tbl_field_name, pk):
        _year = self.date.year
        try:
            _qs = (
                AccountBalance
                .objects
                .get(Q(year=_year) & Q(account_id=pk))
            )

        except AccountBalance.DoesNotExist as e:
            SignalBase.accounts(sender=type(self), instance=None)
            raise e

        _balance_tbl_field_value = getattr(_qs, balance_tbl_field_name)
        _balance_tbl_field_value = self._calc_field(caller, _balance_tbl_field_value)

        setattr(_qs, balance_tbl_field_name, _balance_tbl_field_value)

        _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
        _qs.delta = calc.calc_delta([_qs.have, _qs.balance])

        _qs.save()
