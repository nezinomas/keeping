from dataclasses import dataclass

import pytest
from django.test import override_settings
from django.views.generic import TemplateView
from django_htmx.middleware import HtmxDetails

from ...mixins.tabs import TabViewMixin

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "loaders": [
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "tab.html": "tab={{ tab }}",
                        "fragment.html": "fragment {{ shell }} {{ content }}",
                        "page.html": "page {{ shell }} {{ content }}",
                    },
                )
            ]
        },
    }
]


@dataclass(frozen=True)
class Tab:
    name: str = "index"
    template_name: str = "tab.html"


class View(TabViewMixin, TemplateView):
    tab = Tab()
    fragment_template = "fragment.html"
    page_template = "page.html"

    def page_context(self) -> dict:
        return {"shell": "nav"}


def _get(rf, **headers):
    request = rf.get("/tab/", headers=headers)
    request.htmx = HtmxDetails(request)
    return View.as_view()(request).content.decode().strip()


@pytest.fixture(autouse=True)
def _templates():
    with override_settings(TEMPLATES=TEMPLATES):
        yield


def test_a_plain_request_gets_the_page_around_the_tab(rf):
    assert _get(rf) == "page nav tab=index"


def test_an_htmx_request_gets_the_fragment(rf):
    assert _get(rf, HX_Request="true") == "fragment nav tab=index"


def test_an_htmx_history_restore_gets_the_whole_page(rf):
    content = _get(rf, HX_Request="true", HX_History_Restore_Request="true")

    assert content == "page nav tab=index"


def test_the_page_context_defaults_to_nothing(rf):
    class Bare(View):
        page_context = TabViewMixin.page_context

    request = rf.get("/tab/")
    request.htmx = HtmxDetails(request)

    assert Bare.as_view()(request).content.decode().strip() == "page  tab=index"
