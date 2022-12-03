import contextlib
from typing import Dict

import pandas as pd
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from pandas import DataFrame as DF

from ..core.lib.balance import Balance
from ..core.lib.balance_table_update import UpdatetBalanceTable
from .conf import Conf
from .lib import utils


class SignalBase():
    def __init__(self, conf: Conf, update_on_load: bool = True):
        self._conf = conf

        if update_on_load:
            self._update()

    @classmethod
    def accounts(cls,
                 sender: object,
                 instance: object,
                 created: bool,
                 signal: str,
                 update_on_load: bool = True):

        _hooks = {
            'incomes.Income': [
                {
                    'method': 'incomes',
                    'category': 'account',
                    'balance_field': 'incomes',
                },
            ],
            'expenses.Expense': [
                {
                    'method': 'expenses',
                    'category': 'account',
                    'balance_field': 'expenses',
                },
            ],
            'debts.Debt': [
                {
                    'method': 'incomes',
                    'category': 'account',
                    'balance_field': 'incomes',
                    'skip': 'lend',
                }, {
                    'method': 'expenses',
                    'category': 'account',
                    'balance_field': 'expenses',
                    'skip': 'borrow',
                },
            ],
            'debts.DebtReturn': [
                {
                    'method': 'incomes',
                    'category': 'account',
                    'balance_field': 'incomes',
                    'skip': 'borrow',
                }, {
                    'method': 'expenses',
                    'category': 'account',
                    'balance_field': 'expenses',
                    'skip': 'lend',
                },
            ],
            'transactions.Transaction': [
                {
                    'method': 'incomes',
                    'category': 'to_account',
                    'balance_field': 'incomes'
                }, {
                    'method': 'expenses',
                    'category': 'from_account',
                    'balance_field': 'expenses',
                },
            ],
            'transactions.SavingClose': [
                {
                    'method': 'incomes',
                    'category': 'to_account',
                    'balance_field': 'incomes',
                },
            ],
            'savings.Saving': [
                {
                    'method': 'expenses',
                    'category': 'account',
                    'balance_field': 'expenses',
                },
            ],
            'bookkeeping.AccountWorth': [
                {
                    'method': 'have',
                    'category': 'account',
                    'balance_field': 'have',
                },
            ]
        }

        _conf = Conf(
            sender=sender,
            instance=instance,
            created=created,
            signal=signal,
            tbl_categories=apps.get_model('accounts.Account'),
            tbl_balance=apps.get_model('accounts.AccountBalance'),
            hooks=_hooks,
            balance_class_method='accounts',
            balance_model_fk_field='account_id'
        )
        return cls(conf=_conf, update_on_load=update_on_load)

    @classmethod
    def savings(cls,
                sender: object,
                instance: object,
                created: bool,
                signal: str,
                update_on_load: bool = True):

        _hooks = {
            'savings.Saving': [
                {
                    'method': 'incomes',
                    'category': 'saving_type',
                    'balance_field': 'incomes.fee',
                },
            ],
            'transactions.SavingClose': [
                {
                    'method': 'expenses',
                    'category': 'from_account',
                    'balance_field': '-incomes.fee',
                },
            ],
            'transactions.SavingChange': [
                {
                    'method': 'incomes',
                    'category': 'to_account',
                    'balance_field': 'incomes',
                }, {
                    'method': 'expenses',
                    'category': 'from_account',
                    'balance_field': '-incomes.fee',
                },
            ],
            'bookkeeping.SavingWorth': [
                {
                    'method': 'have',
                    'category': 'saving_type',
                    'balance_field': 'market_value',
                },
            ],
        }

        _conf = Conf(
            sender=sender,
            instance=instance,
            created=created,
            signal=signal,
            tbl_categories=apps.get_model('savings.SavingType'),
            tbl_balance=apps.get_model('savings.SavingBalance'),
            hooks=_hooks,
            balance_class_method='savings',
            balance_model_fk_field='saving_type_id'
        )
        return cls(conf=_conf, update_on_load=update_on_load)

    @classmethod
    def pensions(cls,
                 sender: object,
                 instance: object,
                 created: bool,
                 signal: str,
                 update_on_load: bool = True):

        _hooks = {
            'pensions.Pension': [
                {
                    'method': 'incomes',
                    'category': 'pension_type',
                    'balance_field': 'incomes.fee',
                },
            ],
            'bookkeeping.PensionWorth': [
                {
                    'method': 'have',
                    'category': 'pension_type',
                    'balance_field': 'market_value',
                },
            ],
        }

        _conf = Conf(
            sender=sender,
            instance=instance,
            created=created,
            signal=signal,
            tbl_categories=apps.get_model('pensions.PensionType'),
            tbl_balance=apps.get_model('pensions.PensionBalance'),
            hooks=_hooks,
            balance_class_method='savings', #balance object same for pensions and savings
            balance_model_fk_field='pension_type_id'
        )
        return cls(conf=_conf, update_on_load=update_on_load)

    def full_balance_update(self) -> None:
        UpdatetBalanceTable(self._conf)

    def _update(self) -> None:
        _hooks = self._conf.get_hook()

        if not _hooks:
            return

        for _hook in _hooks:
            _category = _hook['category']
            _field = _hook['balance_field']

            _account = utils.getattr_(self._conf.instance, _category)
            _account_id = utils.getattr_(_account, 'pk')
            _old_account_id = self._conf.old_values.get(_category)

            # skip debts methods
            if self._skip_debt(_hook):
                continue

            # new
            if self._conf.created:
                try:
                    self._tbl_balance_field_update('new', _field, _account_id)
                    continue
                except ObjectDoesNotExist:
                    return

            # delete
            if self._conf.signal == 'delete':
                try:
                    self._tbl_balance_field_update('delete', _field, _account_id)
                    continue
                except ObjectDoesNotExist:
                    return

            try:
                # account not changed
                if _old_account_id == _account_id:
                    self._tbl_balance_field_update('update', _field, _account_id)
                # account changed
                else:
                    self._tbl_balance_field_update('new', _field, _account_id)
                    self._tbl_balance_field_update('delete', _field, _old_account_id)
            except ObjectDoesNotExist:
                return

    def _calc_field(self, /, caller: str, field: str = 'price') -> float:
        val = float(self._conf.get_values(field))
        val_old = float(self._conf.get_old_values(field))

        _switch = {
            'new': val,
            'update': - val_old + val,
            'delete': - val_old
        }
        return _switch.get(caller, 0.0)

    def _tbl_balance_field_update(self, caller: str, balance_tbl_field_name: str, pk: int) -> None:
        _year = self._conf.instance.date.year
        try:
            _qs = (
                self._conf.tbl_balance
                .objects
                .get(Q(year=_year) & Q(**{self._conf.balance_model_fk_field: pk}))
            )
        except ObjectDoesNotExist as e:
            self.full_balance_update()
            raise e

        _df = self._update_values(_qs, caller, balance_tbl_field_name)

        # recalculate accounts
        if 'accounts' in self._conf.balance_class_method:
            _df = Balance.recalc_accounts(_df)

            self._save_object(_qs, _df)
            return

        # recalculate savings
        if 'savings' in self._conf.balance_class_method:
            # update incomes on SavingClose, SavingChange
            if '-incomes' in balance_tbl_field_name:
                _df.at[0, 'incomes'] = _df.at[0, 'incomes'] - self._calc_field(caller, field='price')

            _df = Balance.recalc_savings(_df)

            self._save_object(_qs, _df)
            return

    def _update_values(self, obj: object, caller: str, balance_tbl_field_name: str) -> DF:
        obj_values = {k: v for k, v in obj.__dict__.items() if '_state' not in k}
        _df = pd.DataFrame([obj_values])

        # update balance table fields
        fields = balance_tbl_field_name.split('.')
        for field in fields:
            _field_name = 'price' if field != 'fee' else 'fee'

            with contextlib.suppress(KeyError):
                # [have,market_value] fields have no start value
                _start = 0.0 if field in ['have', 'market_value'] else _df.at[0, field]
                _df.at[0, field] = _start + self._calc_field(caller, field=_field_name)
        return _df

    def _save_object(self, obj: object, df: DF) -> None:
        # update get query object values and save object
        _qs_updated_values = df.to_dict('records')[0]
        obj.__dict__.update(_qs_updated_values)
        obj.save()

    def _skip_debt(self, hook: Dict) -> bool:
        _debt_type = utils.getattr_(self._conf.instance, "debt_type")

        if not _debt_type:
            if _debt := utils.getattr_(self._conf.instance, 'debt'):
                _debt_type= utils.getattr_(_debt, "debt_type")

        _skip = hook.get('skip')

        if _debt_type and _debt_type == _skip:
            return True

        return False
