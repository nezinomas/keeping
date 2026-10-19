import factory
from django.db.models import signals

from ...journals.tests.factories import JournalFactory
from ..models import Account, AccountBalance


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account
        django_get_or_create = ("title",)

    journal = factory.SubFactory(JournalFactory)
    title = "Account1"
    closed = None


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
