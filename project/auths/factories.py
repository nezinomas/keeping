import factory
from django.db.models.signals import post_save

from ..auths.models import User


@factory.django.mute_signals(post_save)
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = 'bob'
    password = factory.PostGenerationMethodCall('set_password', '123')
    email = 'bob@bob.com'
    year = 1999
    month = 12
