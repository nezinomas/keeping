import os
import shutil
import tempfile

import pytest
from django.conf import settings
from django.test import override_settings
from django.utils.text import slugify
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


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@pytest.mark.xfail
def test_count_type_unique_for_user(main_user):
    CountType.objects.create(title='T', user=main_user)
    CountType.objects.create(title='T', user=main_user)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_unique_for_users(main_user, second_user):
    CountType.objects.create(title='T', user=main_user)
    CountType.objects.create(title='T', user=second_user)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_related(main_user, second_user):
    CountTypeFactory(title='X1', user=main_user)
    CountTypeFactory(title='X2', user=second_user)

    actual = CountType.objects.related()

    assert actual.count() == 1
    assert actual[0].title == 'X1'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_items(main_user, second_user):
    CountTypeFactory(title='X1', user=main_user)
    CountTypeFactory(title='X2', user=second_user)

    actual = CountType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'X1'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
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


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
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


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_update():
    obj = CountTypeFactory(title='XXX')
    CountFactory(counter_type=slugify('XXX'))

    assert Count.objects.count() == 1
    assert Count.objects.first().counter_type == 'xxx'

    obj.title = 'YYY'
    obj.save()

    assert CountType.objects.count() == 1
    assert CountType.objects.first().title == 'YYY'

    assert Count.objects.count() == 1
    assert Count.objects.first().counter_type == 'yyy'


# ---------------------------------------------------------------------------------------
#                                                                           generate menu
# ---------------------------------------------------------------------------------------
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch('project.counts.models.render_to_string')
@patch('builtins.open')
def test_menu_create_journal_id_folder(open_mock, render_mock, get_user):
    journal_pk = str(get_user.journal.pk)
    folder = os.path.join(settings.MEDIA_ROOT, journal_pk)

    # delete journal_pk folder
    if os.path.isdir(folder):
        shutil.rmtree(folder)

    assert not os.path.isdir(folder)

    CountTypeFactory()

    assert os.path.isdir(folder)
    assert render_mock.call_count == 1
    assert open_mock.call_count == 1

    shutil.rmtree(folder)
