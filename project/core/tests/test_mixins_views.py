from types import SimpleNamespace

import pytest

from ..mixins import views


@pytest.mark.xfail
def test_queryset_fail():
    class Dummy(views.GetQuerysetMixin):
        model = SimpleNamespace(objects=SimpleNamespace())

    Dummy().get_queryset()


def test_queryset_retun_qs():
    class Dummy(views.GetQuerysetMixin):
        model = SimpleNamespace(objects=SimpleNamespace(related=lambda: 'xxx'))

    actual = Dummy().get_queryset()

    assert actual == 'xxx'
