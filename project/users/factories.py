from datetime import datetime

import factory
import pytz
from django.contrib.auth.hashers import make_password

from ..users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username', )

    username = 'bob'
    password = factory.LazyFunction(lambda: make_password('123'))
    email = 'bob@bob.com'
    year = 1999
    month = 12
    date_joined = datetime(1999, 1, 1, tzinfo=pytz.utc)
