from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from ...accounts.lib.balance import Balance
from ...bookkeeping.lib import helpers as calc
from ..lib.balance_table_update import UpdatetBalanceTable


# {app.model_name: {accountbalance_table_field: model_field}}
# model must have same methods as account_balance_table_field
# i.e. Incomes.objects.incomes()
HOOKS = {
    'incomes.Income': {
        'incomes': 'account',
    },
    'expenses.Expense': {
        'expenses': 'account',
    },
    'debts.Lent': {
        'incomes': 'account',
    },
    'debts.LentReturn': {
        'expenses': 'account',
    },
    'debts.Borrow': {
        'expenses': 'account',
    },
    'debts.BorrowReturn': {
        'incomes': 'account',
    },
    'transactions.Transaction': {
        'incomes': 'to_account',
        'expenses': 'from_account',
    },
    'savings.Saving': {
        'expenses': 'account',
    },
    'transactions.SavingClose': {
        'incomes': 'to_account',
    },
    'bookkeeping.AccountWorth': {
        'have': 'account',
    }
}

def _getattr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except AttributeError:
        return default


class AccountBalanceMixin():
    original_price = 0.0
    old_values = {}

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
        print(f'\n\n## save method {self.price=} {self.date=}')
        self.update_accountbalance_table('update')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        print('\n\n## delete method')
        self.update_accountbalance_table()

    def update_accountbalance_table(self, caller: str = None):
        _arr = self.__class__.__module__.split('.') # [0]=project [1]=app
        _name = f'{_arr[1]}.{type(self).__name__}' # = app.Model
        _hook = HOOKS.get(_name)

        if not _hook:
            return

        for _balance_tbl_field_name, _account_name in _hook.items():
            _account = getattr(self, _account_name)
            _old_account_id = self.old_values.get(_account_name)

            if not _old_account_id or _old_account_id == _account.pk:
                try:
                    caller = caller if caller else 'delete'
                    print(
                        f'\n\n>>>{caller=} {_hook=} {_balance_tbl_field_name=} {_account_name=} {_account.pk=} {_old_account_id=}')
                    self._update_balance_tbl(caller, _balance_tbl_field_name, _account.pk)
                except ObjectDoesNotExist:
                    return
            else:
                try:
                    print(f'\n\n>>> caller: {_hook=} new {_account.pk=}')
                    self._update_balance_tbl('new', _balance_tbl_field_name ,_account.pk)
                    print(f'\n\n>>> caller: {_hook=} delete {_old_account_id=}')
                    self._update_balance_tbl('delete', _balance_tbl_field_name, _old_account_id)
                except ObjectDoesNotExist:
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
                apps.get_model('accounts.AccountBalance')
                .objects
                .get(Q(year=_year) & Q(account_id=pk))
            )

        except ObjectDoesNotExist as e:
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nquery failed -> UPDATE ACCOUNT CLASS CALLED\n')
            UpdatetBalanceTable(category_table='accounts.Account',
                                      balance_table='accounts.AccountBalance',
                                      balance_object=Balance,
                                      hooks=HOOKS)
            raise e

        print(
            f'\n\nquery before save:\n{_qs.year=}\n{_qs.past=}\n{_qs.incomes=}\n{_qs.expenses=}\n{_qs.have=}')
        _balance_tbl_field_value = getattr(_qs, balance_tbl_field_name)
        _balance_tbl_field_value = self._calc_field(
            caller, _balance_tbl_field_value)

        setattr(_qs, balance_tbl_field_name, _balance_tbl_field_value)

        _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
        _qs.delta = calc.calc_delta([_qs.have, _qs.balance])

        print(
            f'\n\nquery after save:\n{_qs.year=}\n{_qs.past=}\n{_qs.incomes=}\n{_qs.expenses=}\n{_qs.have=}')
        _qs.save()
