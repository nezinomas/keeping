import pytest
from mock import patch

from ..factories import CountFactory, CountTypeFactory
from ..models import Count, CountType

pytestmark = pytest.mark.django_db

# ---------------------------------------------------------------------------------------
#                                                                                   Count
# --------------------------------------------------------------------------------------
def test_count_str():
    actual = CountFactory.build()

    assert str(actual) == '1999-01-01: 1'


# ---------------------------------------------------------------------------------------
#                                                                              Count Type
# ---------------------------------------------------------------------------------------
def test_count_type_str():
    obj = CountTypeFactory.build()

    assert str(obj) == 'Count Type'


@pytest.mark.xfail
def test_count_type_unique_for_user(main_user):
    CountType.objects.create(title='T', user=main_user)
    CountType.objects.create(title='T', user=main_user)


def test_count_type_unique_for_users(main_user, second_user):
    CountType.objects.create(title='T', user=main_user)
    CountType.objects.create(title='T', user=second_user)


def test_count_type_related(main_user, second_user):
    CountTypeFactory(title='X1', user=main_user)
    CountTypeFactory(title='X2', user=second_user)

    actual = CountType.objects.related()

    assert actual.count() == 1
    assert actual[0].title == 'X1'


def test_count_type_items(main_user, second_user):
    CountTypeFactory(title='X1', user=main_user)
    CountTypeFactory(title='X2', user=second_user)

    actual = CountType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'X1'


@patch('project.core.lib.utils.get_request_kwargs', return_value='x1')
def test_count_type_not_update_other_user_count(mck, main_user, second_user):
    u1 = CountTypeFactory(title='X1', user=main_user)
    u2 = CountTypeFactory(title='X1', user=second_user)

    obj1 = CountFactory(counter_type=u1.slug, user=main_user)
    obj2 = CountFactory(counter_type=u2.slug, user=second_user)

    u1.title = 'X2'
    u1.save()

    assert Count.objects.get(pk=obj1.pk).counter_type == 'x2'
    assert Count.objects.get(pk=obj2.pk).counter_type == 'x1'


@patch('project.core.lib.utils.get_request_kwargs', return_value='x1')
def test_count_type_not_delete_other_user_count(mck, main_user, second_user):
    u1 = CountTypeFactory(title='X1', user=main_user)
    u2 = CountTypeFactory(title='X1', user=second_user)

    CountFactory(counter_type=u1.slug, user=main_user)
    CountFactory(counter_type=u2.slug, user=second_user)

    u1.delete()

    assert Count.objects.count() == 1
    assert Count.objects.first().counter_type == 'x1'
    assert Count.objects.first().user == second_user
