from dataclasses import dataclass
from typing import Dict

from django.db.models import Model


@dataclass
class Conf():
    created: bool
    signal: str
    balance_class_method: str
    balance_model_fk_field: str
    tbl_categories: Model
    tbl_balance: Model
    hooks: Dict
    sender: object
    instance: object

    def get_hook(self):
        _app = self.sender.__module__.split('.')[1]
        _model = self.sender.__name__
        _hook = self.hooks.get(f'{_app}.{_model}')

        return _hook

    def get_old_values(self, name, default=None):
        return self.instance.old_values.get(name, default)
