import factory
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from ..auths.models import Profile


@factory.django.mute_signals(post_save)
class ProfileFactory(factory.DjangoModelFactory):

    class Meta:
        model = Profile
        django_get_or_create = ('user', )

    user = factory.SubFactory('project.core.factories.UserFactory', profile=None)
    year = 1999
    month = 12


@factory.django.mute_signals(post_save)
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = 'bob'
    password = factory.PostGenerationMethodCall('set_password', '123')
    email = 'bob@bob.com'

    profile = factory.RelatedFactory(ProfileFactory, 'user')
