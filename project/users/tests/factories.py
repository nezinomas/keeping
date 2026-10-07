from datetime import datetime

import factory
import pytz
from django.conf import settings
from django.contrib.auth.hashers import make_password

from ...users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)
        skip_postgeneration_save = True

    username = "bob"
    password = factory.LazyFunction(lambda: make_password("123"))
    email = "bob@bob.com"
    year = 1999
    month = 12
    date_joined = datetime(1999, 1, 1, tzinfo=pytz.utc)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        passed = "journal" in kwargs
        user = super()._create(model_class, *args, **kwargs)

        if not passed:
            user.journal.lang = settings.LANGUAGE_CODE
            user.journal.save()

        return user
