import factory

from .models import Account


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = Account
        django_get_or_create = ('title',)

    title = 'Account1'
