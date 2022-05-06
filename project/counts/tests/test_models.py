import os
import shutil
import tempfile
from datetime import date

import pytest
from django.conf import settings
from django.test import override_settings
from mock import patch

from ..factories import CountFactory, CountTypeFactory
from ..models import Count, CountType

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                   Count
# --------------------------------------------------------------------------------------
@pytest.fixture()
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def _counters(second_user):
    CountFactory(date=date(1999, 1, 1), quantity=1.0)
    CountFactory(date=date(1999, 1, 1), quantity=1.5)
    CountFactory(date=date(1999, 2, 1), quantity=2.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)

    # second CountType for same user
    CountFactory(date=date(1999, 1, 1), quantity=1,
                 count_type=CountTypeFactory(title='Z'))

    # second user
    CountFactory(
        date=date(1999, 2, 1), quantity=100.0,
        count_type=CountTypeFactory(title='X'),
        user=second_user
    )


@pytest.fixture()
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def _different_users(second_user):
    CountFactory()
    CountFactory(count_type=CountTypeFactory(title='X'))
    CountFactory(count_type=CountTypeFactory(title='X'), user=second_user)


def test_count_str():
    actual = CountFactory.build()

    assert str(actual) == '1999-01-01: 1'


def test_count_related(_different_users):
    actual = Count.objects.related()

    assert len(actual) == 2
    assert actual[0].user.username == 'bob'


def test_count_items(_different_users):
    actual = Count.objects.items()

    assert len(actual) == 2
    assert actual[0].user.username == 'bob'


def test_count_items_with_count_type(_different_users):
    actual = Count.objects.items(count_type='count-type')

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_count_year(_different_users):
    actual = list(Count.objects.year(1999))

    assert len(actual) == 2
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == 'bob'


def test_count_year_with_count_type(_different_users):
    actual = list(Count.objects.year(1999, count_type='count-type'))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == 'bob'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_quantity_float():
    p = CountFactory(quantity=0.5)

    p.full_clean()

    assert str(p) == '1999-01-01: 0.5'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_quantity_int():
    p = CountFactory(quantity=5)

    p.full_clean()

    assert str(p) == '1999-01-01: 5.0'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_order():
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 12, 1))

    actual = list(Count.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


def test_count_quantity_for_one_year(_counters):
    actual = Count.objects\
            .sum_by_year(year=1999, count_type='count-type')
    actual = list(actual)

    assert actual[0]['qty'] == 5.5


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_quantity_for_all_years(_counters):
    CountFactory(date=date(2020, 1, 1), quantity=10)
    CountFactory(date=date(2020, 12, 1), quantity=5)

    actual = Count.objects.sum_by_year(count_type='count-type')
    actual = list(actual)

    assert actual[0]['qty'] == 5.5
    assert actual[1]['qty'] == 15


def test_count_days_quantity_sum(_counters):
    actual = Count.objects\
            .sum_by_day(1999, count_type='count-type')

    actual = actual.values_list('qty', flat=True)

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_count_days_quantity_sum_for_january(_counters):
    actual = Count.objects\
            .sum_by_day(year=1999, month=1, count_type='count-type')
    actual = actual.values_list('qty', flat=True)

    expect = [2.5]

    assert expect == pytest.approx(actual, rel=1e-2)


# ---------------------------------------------------------------------------------------
#                                                                              Count Type
# ---------------------------------------------------------------------------------------
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
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

    obj1 = CountFactory(count_type=u1, user=main_user)
    obj2 = CountFactory(count_type=u2, user=second_user)

    u1.title = 'X2'
    u1.save()

    assert Count.objects.get(pk=obj1.pk).count_type.slug == 'x2'
    assert Count.objects.get(pk=obj2.pk).count_type.slug == 'x1'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch('project.core.lib.utils.get_request_kwargs', return_value='x1')
def test_count_type_not_delete_other_user_count(mck, main_user, second_user):
    u1 = CountTypeFactory(title='X1', user=main_user)
    u2 = CountTypeFactory(title='X1', user=second_user)

    CountFactory(count_type=u1, user=main_user)
    CountFactory(count_type=u2, user=second_user)

    u1.delete()

    assert Count.objects.count() == 1
    assert Count.objects.first().count_type.slug == 'x1'
    assert Count.objects.first().user == second_user


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_update():
    obj = CountTypeFactory(title='XXX')
    CountFactory(count_type=obj)

    assert Count.objects.count() == 1
    assert Count.objects.first().count_type.title == 'XXX'

    obj.title = 'YYY'
    obj.save()

    assert CountType.objects.count() == 1
    assert CountType.objects.first().title == 'YYY'

    assert Count.objects.count() == 1
    assert Count.objects.first().count_type.title == 'YYY'


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
