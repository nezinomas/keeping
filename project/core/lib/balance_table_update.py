from django.apps import apps


class UpdatetBalanceTable():
    def __init__(self, category_table, balance_table, balance_object, hooks):
        self._balance_model = apps.get_model(balance_table)
        self._hooks = hooks
        self._balance_object = balance_object

        self._accounts = self._get_accounts(category_table)

        self._calc()

    def _get_accounts(self, category_table):
        a = apps.get_model(category_table).objects.related()
        return {obj.id: obj for obj in a}

    def _get_data(self):
        _data = []
        _models = list(self._hooks.keys())

        for _model_name in _models:
            try:
                model = apps.get_model(_model_name)
            except LookupError:
                continue

            for _method, _ in self._hooks[_model_name].items():
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

        self._balance_object.create_balance(data=_data)

        _df = self._balance_object.balance_df

        _update = []
        _create = []
        _delete = []
        _link = {}

        _items = self._balance_model.objects.items()
        if not _items.exists():
            _dicts = self._balance_object.balance

            # get name. it must be account_id|saving_type_id|pension_type_id
            if _dicts:
                for x in _dicts[0].keys():
                    _key_name = x if '_id' in x else None

            for _dict in _dicts:
                _id = _dict[_key_name]
                _create.append(self._balance_model(account=self._accounts.get(_id), **_dict))
        else:
            _link = self._balance_object.year_account_link

            for _row in _items:
                try:
                    _df_row = _df.loc[(_row.year, _row.account_id)].to_dict()
                except KeyError:
                    _delete.append(_row.pk)
                    continue

                _obj = self._balance_model(
                    pk=_row.pk,
                    year=_row.year,
                    account=self._accounts.get(_row.account_id),
                    **_df_row)

                _update.append(_obj)

                # remove id in link
                _link.get(_row.year).remove(_row.account_id)

        # if in _link {year: [account_id]} left some id, create records
        for _year, _arr in _link.items():
            for _id in _arr:
                _df_row = _df.loc[(_year, _id)].to_dict()
                _obj = self._balance_model(year=_year, account=self._accounts.get(_id), **_df_row)
                _create.append(_obj)

        if _create:
            self._balance_model.objects.bulk_create(_create)

        if _update:
            self._balance_model.objects.bulk_update(_update, _df.columns.values.tolist())

        if _delete:
            self._balance_model.objects.related().filter(pk__in=_delete).delete()
