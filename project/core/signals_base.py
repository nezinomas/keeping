import pandas as pd
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from ..core.lib.balance import Balance
from ..core.lib.balance_table_update import UpdatetBalanceTable
from .conf import Conf


class SignalBase():
    def __init__(self, conf: Conf):
        self._conf = conf

        self._update()

    @classmethod
    def accounts(cls, sender: object, instance: object, created: bool, signal: str):
        _hooks = {
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

        _conf = Conf(
            balance_class_method='accounts',
            balance_model_fk_field='account_id',
            created=created,
            signal=signal,
            tbl_categories=apps.get_model('accounts.Account'),
            tbl_balance=apps.get_model('accounts.AccountBalance'),
            sender=sender,
            instance=instance,
            hooks=_hooks
        )
        return cls(conf=_conf)

    @classmethod
    def savings(cls, sender: object, instance: object, created: bool, signal: str):
        _hooks = {
            'savings.Saving': {
                'incomes': 'saving_type',
            },
            'transactions.SavingClose': {
                'expenses': 'from_account',
            },
        }

        _conf = Conf(
            balance_class_method='savings',
            balance_model_fk_field='saving_type_id',
            created=created,
            signal=signal,
            tbl_categories=apps.get_model('savings.SavingType'),
            tbl_balance=apps.get_model('savings.SavingBalance'),
            sender=sender,
            instance=instance,
            hooks=_hooks
        )
        return cls(conf=_conf)

    @classmethod
    def pensions(cls, sender: object, instance: object, created: bool, signal: str):
        _hooks = {
            'pensions.Pension': {
                'incomes': 'pension_type',
            },
        }

        _conf = Conf(
            balance_class_method='savings', #balance object same for pensions and savings
            balance_model_fk_field='pension_type_id',
            created=created,
            signal=signal,
            tbl_categories=apps.get_model('pensions.PensionType'),
            tbl_balance=apps.get_model('pensions.PensionBalance'),
            sender=sender,
            instance=instance,
            hooks=_hooks
        )
        return cls(conf=_conf)

    def _update(self):
        _hook = self._conf.get_hook()
        if not _hook:
            return

        for _balance_tbl_field_name, _account_name in _hook.items():
            _account = getattr(self._conf.instance, _account_name)
            _old_account_id = self._conf.instance.old_values.get(_account_name)

            # new
            if self._conf.created:
                try:
                    print('<<< try new')
                    self._tbl_balance_field_update('new', _balance_tbl_field_name, _account.pk)
                except ObjectDoesNotExist:
                    return
                continue

            # delete
            if self._conf.signal == 'delete':
                try:
                    print('<<< try delete')
                    self._tbl_balance_field_update('delete', _balance_tbl_field_name, _account.pk)
                except ObjectDoesNotExist:
                    return
                continue

            # update
            if _old_account_id == _account.pk:
                # account not changed
                try:
                    print('<<< try update account not changed')
                    self._tbl_balance_field_update('update', _balance_tbl_field_name, _account.pk)
                except ObjectDoesNotExist:
                    return
            else:
                # account changed
                try:
                    print('<<< try update account changed')
                    self._tbl_balance_field_update('new', _balance_tbl_field_name, _account.pk)
                    self._tbl_balance_field_update('delete', _balance_tbl_field_name, _old_account_id)
                except ObjectDoesNotExist:
                    return

    def _calc_field(self, /, caller, field = 'price'):
            price = float(getattr(self._conf.instance, field))
            original_price = float(self._conf.get_old_values(field, 0.0))

            _switch = {
                'new': price,
                'update': - original_price + price,
                'delete': - original_price
            }
            return _switch.get(caller, 0.0)

    def _tbl_balance_field_update(self, caller, balance_tbl_field_name, pk):
        _year = self._conf.instance.date.year
        try:
            _qs = (
                self._conf.tbl_balance
                .objects
                .get(Q(year=_year) & Q(**{self._conf.balance_model_fk_field: pk}))
            )

        except ObjectDoesNotExist as e:
            print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nquery failed -> UPDATE ACCOUNT CLASS CALLED\n')
            UpdatetBalanceTable(self._conf)
            raise e

        _qs_values = {k: v for k, v in _qs.__dict__.items() if not '_state' in k}
        print(f'>>> qs loaded values\n{_qs_values}\n')
        _df = pd.DataFrame([_qs_values])

        # print(f'\n>>> df loaded\n{_df}\n')
        _df.at[0, balance_tbl_field_name] = (
            _df.at[0, balance_tbl_field_name] + self._calc_field(caller, field='price')
        )

        if 'accounts' in self._conf.balance_class_method:
            _df = Balance.recalc_accounts(_df)
        else:
            # update fee
            if self._conf.get_old_values('fee') is not None:
                _df.at[0, 'fee'] = _df.at[0, 'fee'] + self._calc_field(caller, field='fee')

            _df = Balance.recalc_savings(_df)

        _qs_updated_values = _df.to_dict('records')[0]
        print(f'>>> qs before save\n{_qs_updated_values}\n')
        _qs.__dict__.update(_qs_updated_values)
        _qs.save()
