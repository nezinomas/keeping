from dataclasses import dataclass
from typing import Dict

from django.db.models import Model

from .lib import utils


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

    def get_old_values(self, name):
        return self.instance.old_values.get(name, 0.0)

    def get_values(self, name):
        val = utils._getattr(self.instance, name, 0.0)

        if val is None:
            val = 0.0

        return val
