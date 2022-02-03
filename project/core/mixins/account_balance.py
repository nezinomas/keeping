from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from ...accounts.lib.balance_new import BalanceNew
from ...bookkeeping.lib import helpers as calc
from ..signals_base import SignalBase

'''
{app.model_name: {accountbalance_table_field: model_field}}

model must have same methods as account_balance_table_field

'''

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

        self.update_accountbalance_table('update')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

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
                    self._update_balance_tbl(caller, _balance_tbl_field_name, _account.pk)
                except ObjectDoesNotExist:
                    return
            else:
                try:
                    self._update_balance_tbl('new', _balance_tbl_field_name ,_account.pk)
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
            print('\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUPDATE ACCOUNT CLASS CALLED\n')
            '''
            SignalBase.accounts(sender=type(self), instance=None, year=_year)
            '''
            UpdateAccountBalanceTable()
            # '''
            raise e

        _balance_tbl_field_value = getattr(_qs, balance_tbl_field_name)
        _balance_tbl_field_value = self._calc_field(caller, _balance_tbl_field_value)

        setattr(_qs, balance_tbl_field_name, _balance_tbl_field_value)

        _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
        _qs.delta = calc.calc_delta([_qs.have, _qs.balance])

        _qs.save()


class UpdateAccountBalanceTable():
    def __init__(self):
        self._accounts = self._accounts_()
        print(f'{self._accounts=}\n\n')
        self._calc()

    def _accounts_(self):
        a = apps.get_model('accounts.Account').objects.items()
        return {obj.id: obj for obj in a}

    def _calc(self):
        _data = []
        _models = list(HOOKS.keys())

        for _model_name in _models:
            try:
                model = apps.get_model(_model_name)
            except LookupError:
                continue

            for _method, _ in HOOKS[_model_name].items():
                try:
                    _method = getattr(model.objects, _method)
                    _qs = _method()
                    if _qs:
                        _data.append(_qs)

                except AttributeError:
                    pass

        if not _data:
            return

        _balance_model = apps.get_model('accounts.AccountBalance')
        _balance = BalanceNew(data=_data)
        _link = {}
        _df = _balance.balance_df
        print(f'\n@ calculated balance\n{_df}\n')

        _update = []
        _create = []
        _delete = []

        _items = _balance_model.objects.items()
        print(f'\nbalance table items\n{_items.values()}')
        if not _items.exists():
            _dicts = _balance.balance
            for _dict in _dicts:
                _id = _dict['account_id']
                del _dict['account_id']

                _create.append(_balance_model(account=self._accounts.get(_id), **_dict))
        else:
            _link = _balance.year_account_link
            print(f'links on load: {_link=}\n')
            for _row in _items:
                print(f'{_row=}')
                try:
                    _df_row = _df.loc[(_row.year, _row.account_id)].to_dict()
                    _update.append(
                        _balance_model(
                            pk=_row.pk,
                            year=_row.year,
                            account=self._accounts.get(_row.account_id),
                            **_df_row)
                    )
                    _update.append(_row)
                    # remove id in link
                    _link.get(_row.year).remove(_row.account_id)
                except KeyError:
                    _delete.append(_row.pk)

        # if in year:account_id link dict left some id, create records
        print(f'links final: {_link=}\n')
        for _year, _arr in _link.items():
            for x in _arr:
                _df_row = _df.loc[(_year, x)].to_dict()
                # print(f'----------------->{_year=} {x=} {_df_row}')
                _create.append(_balance_model(year=_year, account=self._accounts.get(x), **_df_row))


        if _create:
            print('\n\n------------------- create event\n', _create)
            _balance_model.objects.bulk_create(_create)
            print(f'{_balance_model.objects.values()}')

        if _update:
            print(f'\n\n------------------- update event\n{_update}')
            _balance_model.objects.bulk_update(_update, ['past', 'incomes', 'expenses', 'balance', 'have', 'delta'])

        if _delete:
            print(f'\n\n------------------- delete event\n{_delete=}')
            _balance_model.objects.related().filter(pk__in=_delete).delete()
