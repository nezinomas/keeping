import pytest
from django.contrib.auth.models import AnonymousUser

from ..context import counts_menu
from .factories import CountTypeFactory

pytestmark = pytest.mark.django_db


def test_counts_menu_lists_the_users_counters(main_user, rf):
    CountTypeFactory(title="XXX", user=main_user)
    request = rf.get("/")
    request.user = main_user

    actual = counts_menu(request)

    assert [count_type.title for count_type in actual["counts_menu"]] == ["XXX"]


def test_counts_menu_of_an_anonymous_user_is_empty(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    assert counts_menu(request) == {"counts_menu": []}
