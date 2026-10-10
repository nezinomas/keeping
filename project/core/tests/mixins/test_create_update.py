import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name, trigger",
    [
        pytest.param("incomes:new", "reload", id="closing_reloads"),
        pytest.param("incomes:type_new", "", id="no_trigger"),
    ],
)
def test_modal_form_renders_its_close_trigger(client_logged, url_name, trigger):
    content = client_logged.get(reverse(url_name)).content.decode("utf-8")

    assert f'data-hx-trigger-form="{trigger}"' in content
