import factory
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save

from ..users.models import User


@factory.django.mute_signals(post_save)
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = 'bob'
    password = make_password('123')
    email = 'bob@bob.com'
    year = 1999
    month = 12
    date_joined = '1999-01-01'
