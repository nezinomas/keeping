import tempfile
from django.test import override_settings
from os import path

import pytest
from django.conf import settings
from ..factories import CountTypeFactory
from django.urls import reverse

pytestmark = pytest.mark.django_db
Template = path.join(settings.SITE_ROOT, 'counts/templates/counts/includes/menu.html')


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_menu_count_type_add(client_logged):
    obj = CountTypeFactory(title='XXX')

    url = reverse('counts:counts_empty')
    response = client_logged.get(url, follow=True)

    content = response.content.decode()

    url = reverse("counts:counts_index", kwargs={"count_type": obj.slug})
    assert f'href="{url}">{obj.title}</a></li>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_menu_count_type_add_two(client_logged):
    obj1 = CountTypeFactory(title='XXX')
    obj2 = CountTypeFactory(title='YYY')

    url = reverse('counts:counts_empty')
    response = client_logged.get(url, follow=True)

    content = response.content.decode()

    url1 = reverse("counts:counts_index", kwargs={"count_type": obj1.slug})
    url2 = reverse("counts:counts_index", kwargs={"count_type": obj2.slug})
    assert f'href="{url1}">{obj1.title}</a></li>' in content
    assert f'href="{url2}">{obj2.title}</a></li>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_menu_count_type_delete(client_logged):
    obj1 = CountTypeFactory(title='XXX')
    obj2 = CountTypeFactory(title='YYY')

    url = reverse('counts:counts_empty')
    response = client_logged.get(url, follow=True)

    content = response.content.decode()

    url1 = reverse("counts:counts_index", kwargs={"count_type": obj1.slug})
    url2 = reverse("counts:counts_index", kwargs={"count_type": obj2.slug})
    assert f'href="{url1}">{obj1.title}</a></li>' in content
    assert f'href="{url2}">{obj2.title}</a></li>' in content

    obj2.delete()
    response = client_logged.get(url, follow=True)
    content = response.content.decode()

    assert f'href="{url2}">{obj2.title}</a></li>' not in content
