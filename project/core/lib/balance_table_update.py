from django.apps import apps

from ..conf import Conf
from .balance import Balance


class UpdatetBalanceTable():
    def __init__(self, conf: Conf):
        self._conf = conf
        self._categories = self._get_categories()
        self._category = conf.balance_model_fk_field[:-3]

        self._calc()

    def _get_categories(self):
        a = self._conf.tbl_categories.objects.related()
        return {obj.id: obj for obj in a}

    def _get_data(self):
        _data = []
        _models = list(self._conf.hooks.keys())

        for _model_name in _models:
            try:
                model = apps.get_model(_model_name)
            except LookupError:
                continue

            for _method, _ in self._conf.hooks[_model_name].items():
                try:
                    _method = getattr(model.objects, _method)
                    _qs = _method()
                    if _qs:
                        _data.append(_qs)

                except AttributeError:
                    pass
        return _data

    def _calc(self):
        _data = self._get_data()

        if not _data:
            return

        _balance_object = getattr(Balance, self._conf.balance_class_method)()
        _balance_object.create_balance(data=_data)

        _df = _balance_object.balance_df

        _update = []
        _create = []
        _delete = []
        _link = {}

        _items = self._conf.tbl_balance.objects.items()
        if not _items.exists():
            _dicts = _balance_object.balance

            # get name. it must be account_id|saving_type_id|pension_type_id
            if _dicts:
                for x in _dicts[0].keys():
                    _key_name = x if '_id' in x else None

            for _dict in _dicts:
                _id = _dict[_key_name]
                _dict.update({
                    self._category: self._categories.get(_id)
                })
                _create.append(self._conf.tbl_balance(**_dict))
        else:
            _link = _balance_object.year_account_link

            for _row in _items:
                try:
                    _dict = _df.loc[(_row.year, _row.account_id)].to_dict()
                except KeyError:
                    _delete.append(_row.pk)
                    continue
                _dict.update({
                    'pk': _row.pk,
                    'year': _row.year,
                    self._category: self._categories.get(_row.account_id)
                })
                _obj = self._conf.tbl_balance(**_dict)
                _update.append(_obj)

                # remove id in link
                _link.get(_row.year).remove(_row.account_id)

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
            self._conf.tbl_balance.objects.bulk_create(_create)

        if _update:
            self._conf.tbl_balance.objects.bulk_update(_update, _df.columns.values.tolist())

        if _delete:
            self._conf.tbl_balance.objects.related().filter(pk__in=_delete).delete()
