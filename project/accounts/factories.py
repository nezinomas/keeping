import factory

from .models import Account, AccountBalance


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = Account
        django_get_or_create = ('title',)

    title = 'Account1'


class AccountBalanceFactory(factory.DjangoModelFactory):
    class Meta:
        model = AccountBalance
        # django_get_or_create = ('account',)

    account = factory.SubFactory(AccountFactory)

    year = 1999
    incomes = 6.75
    expenses = 6.5
    delta = 0.25
    have = 0.20
    diff = 0.05
