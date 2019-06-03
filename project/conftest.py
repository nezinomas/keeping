import pytest

from .core.factories import UserFactory


@pytest.fixture(scope='session')
def user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        u = UserFactory()
    yield u
    with django_db_blocker.unblock():
        u.delete()


@pytest.fixture()
def login(client, user):
    client.login(username='bob', password='123')
