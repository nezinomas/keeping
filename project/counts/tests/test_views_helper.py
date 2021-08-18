import pytest

from ..factories import CountTypeFactory
from ..lib import views_helper as H

pytestmark = pytest.mark.django_db


def test_get_object_no_object():
    obj = H.get_object({})

    assert obj.pk == 0
    assert obj.slug == 'counter'
    assert obj.title == 'Nerasta'


def test_get_object():
    obj = CountTypeFactory(title='Xxx')

    actual = H.get_object({'count_type': 'xxx'})

    assert actual.pk == obj.pk
    assert actual.slug == obj.slug
    assert actual.title == obj.title
