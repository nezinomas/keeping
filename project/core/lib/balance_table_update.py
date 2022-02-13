from django.apps import apps

from ..conf import Conf
from .balance import Balance


class UpdatetBalanceTable():
    def __init__(self, conf: Conf):
        self._conf = conf
        self._categories = self._get_categories()
        self._category = conf.balance_model_fk_field[:-3]

        self._update_balance_table()

    def _get_categories(self):
        categories = self._conf.tbl_categories.objects.related()
        print(f'categories\n{categories}')
        return {category.id: category for category in categories}

    def _get_balance(self) -> Balance:
        _balance_object = None
        _data = self._get_data()

        if not _data:
            return _balance_object

        _balance_object = getattr(Balance, self._conf.balance_class_method)()
        _balance_object.create_balance(data=_data)

        return _balance_object

    def _get_data(self):
        _data = []

        for _model, _hooks in self._conf.hooks.items():
            try:
                model = apps.get_model(_model)
            except LookupError:
                continue

            for _hook in _hooks:
                try:
                    _method = getattr(model.objects, _hook['method'])
                    _qs = _method()
                    if _qs:
                        _data.append(_qs)

                except AttributeError:
                    pass
        print(f'\nUpdateBalanceTable._get_data [39] data\n{_data}\n')
        return _data


    def _update_balance_table(self):
        _balance_object = self._get_balance()

        if not _balance_object:
            return

        _df = _balance_object.balance_df

        _update = []
        _create = []
        _delete = []

        _items = self._conf.tbl_balance.objects.items().values()
        _link = _balance_object.year_account_link

        for _row in _items:
            _category_id = _row[self._conf.balance_model_fk_field]
            _year = _row['year']

            try:
                _dict = _df.loc[(_year, _category_id)].to_dict()
            except KeyError:
                _delete.append(_row['id'])
                continue

            _dict.update({
                'pk': _row['id'],
                'year': _year,
                self._category: self._categories.get(_category_id)
            })
            _obj = self._conf.tbl_balance(**_dict)
            _update.append(_obj)

            # remove id in link
            _link.get(_year).remove(_category_id)

        # if in _link {year: [account_id]} left some id, create records
        for _year, _arr in _link.items():
            for _id in _arr:
                _dict = _df.loc[(_year, _id)].to_dict()
                _dict.update({
                    'year': _year,
                    self._category: self._categories.get(_id)
                })
                _obj = self._conf.tbl_balance(**_dict)
                _create.append(_obj)

        if _create:
            print('UpdateBalanceTable >> create')
            self._conf.tbl_balance.objects.bulk_create(_create)

        if _update:
            print('UpdateBalanceTable >> update')
            self._conf.tbl_balance.objects.bulk_update(_update, _df.columns.values.tolist())

        if _delete:
            print('UpdateBalanceTable >> delete')
            self._conf.tbl_balance.objects.related().filter(pk__in=_delete).delete()
