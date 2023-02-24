from datetime import datetime

import factory
import pytz
from django.db import models
from django.db.models import signals

from ..journals.factories import JournalFactory
from .models import Account, AccountBalance


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account
        django_get_or_create = ('title', )

    journal = factory.SubFactory(JournalFactory)
    title = 'Account1'
    closed = None

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        created = kwargs.pop('created', None)

        obj = super()._create(target_class, *args, **kwargs)

        if created is not None:
            obj.created = created
        else:
            obj.created = datetime(1, 1, 1, tzinfo=pytz.utc)

        models.Model.save(obj)

        return obj


@factory.django.mute_signals(signals.post_save)
class AccountBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccountBalance

    account = factory.SubFactory(AccountFactory)

    year = 1999
    past = 1
    incomes = 675
    expenses = 65
    balance = 125
    have = 20
    delta = -105
