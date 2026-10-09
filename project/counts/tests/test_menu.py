import pytest
from django.urls import reverse

from .factories import CountTypeFactory

pytestmark = pytest.mark.django_db


def _link(obj):
    url = reverse("counts:index", kwargs={"slug": obj.slug})
    return f'href="{url}">{obj.title}</a>'


def test_menu_lists_every_count_type(client_logged):
    obj1 = CountTypeFactory(title="XXX")
    obj2 = CountTypeFactory(title="YYY")

    content = client_logged.get(reverse("counts:empty"), follow=True).content.decode()

    assert _link(obj1) in content
    assert _link(obj2) in content


def test_menu_drops_a_deleted_count_type_and_keeps_the_rest(client_logged):
    obj1 = CountTypeFactory(title="XXX")
    obj2 = CountTypeFactory(title="YYY")

    obj2.delete()
    content = client_logged.get(reverse("counts:empty"), follow=True).content.decode()

    assert _link(obj2) not in content
    assert _link(obj1) in content
