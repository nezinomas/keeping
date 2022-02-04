import factory
from django.db.models import Model
from django.utils import timezone
from factory.django import DjangoModelFactory

from ..accounts.factories import AccountFactory
from ..pensions.factories import PensionTypeFactory
from ..savings.factories import SavingTypeFactory
from . import models


class SavingWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.SavingWorth

    saving_type = factory.SubFactory(SavingTypeFactory)
    price = 0.5

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        _date = kwargs.pop('date', None)

        obj = super()._create(target_class, *args, **kwargs)

        if _date is not None:
            obj.date = _date
        else:
            obj.date = timezone.now()

        Model.save(obj)

        return obj

class AccountWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted


class PensionWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.PensionWorth

    pension_type = factory.SubFactory(PensionTypeFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted
