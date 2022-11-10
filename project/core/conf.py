import copy
from dataclasses import dataclass, field
from typing import Dict

from django.db.models import Model

from .lib import utils


@dataclass
class Conf():
    sender: object
    instance: object
    created: bool
    signal: str
    tbl_categories: Model
    tbl_balance: Model
    hooks: Dict
    balance_class_method: str
    balance_model_fk_field: str
    old_values: Dict = field(init=False)

    def __post_init__(self):
        # copy old values to Dictionary
        # when access instance reference object by ForeignKey
        # e.g debt_type=debt_return.debt.type
        # then old_values somehow becomes not debt_return.old_values, but debt.old_values
        # why?
        try:
            self.old_values = copy.copy(self.instance.old_values)
        except AttributeError:
            self.old_values = {}

    def get_hook(self):
        _app = self.sender.__module__.split('.')[1]
        _model = self.sender.__name__
        return self.hooks.get(f'{_app}.{_model}')

    def get_old_values(self, name):
        return self.old_values.get(name, 0.0)

    def get_values(self, name):
        val = utils.getattr_(self.instance, name, 0.0)

        if val is None:
            val = 0.0

        return val
