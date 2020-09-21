import factory

from ..users.factories import UserFactory
from .models import Account, AccountBalance


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account
        django_get_or_create = ('title',)

    title = 'Account1'
    user = factory.SubFactory(UserFactory)


class AccountBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccountBalance
        # django_get_or_create = ('account',)

    account = factory.SubFactory(AccountFactory)

    year = 1999
    past = 1.0
    incomes = 6.75
    expenses = 6.5
    balance = 1.25
    have = 0.20
    delta = -1.05
