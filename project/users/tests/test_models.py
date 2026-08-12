import pytest
from django.core.exceptions import ValidationError

from ...drinks.lib.drink_types import DrinkType
from ..models import User
from ..services.model_services import UserModelService
from .factories import UserFactory

pytestmark = pytest.mark.django_db


def test_drink_type_offers_the_declared_types():
    field = User._meta.get_field("drink_type")

    assert field.choices == DrinkType.choices


def test_an_undeclared_drink_type_does_not_validate():
    field = User._meta.get_field("drink_type")

    with pytest.raises(ValidationError):
        field.clean("grog", UserFactory.build())


def test_user_str():
    actual = UserFactory.build()

    assert str(actual) == "bob"


def test_user_reversed():
    actual = User.objects.first()

    assert User.objects.count() == 1
    assert str(actual.journal) == "bob Journal"


def test_user_related_queries(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(x.journal.title for x in UserModelService(main_user).objects)
