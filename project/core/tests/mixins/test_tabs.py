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
                        "tab.html": "tab={{ tab }} {{ tab_url }}",
                        "fragment.html": "fragment {{ content }}",
                        "page.html": (
                            "page {{ page_title }}"
                            "{% for tab, url in tabs %} {{ tab.name }}={{ url }}"
                            "{% endfor %} {{ content }}"
                        ),
                    },
                ),
                "django.template.loaders.app_directories.Loader",
            ]
        },
    }
]


@dataclass(frozen=True)
class Tab:
    name: str
    title: str
    template_name: str = "tab.html"

    @property
    def url(self) -> str:
        return f"/{self.name}/"


INDEX = Tab("index", "Overview")
DATA = Tab("data", "Data")


class Shop(TabViewMixin, TemplateView):
    tabs = (INDEX, DATA)
    default_tab = INDEX
    app_title = "Shop"
    page_template = "page.html"


class View(Shop):
    fragment_template = "fragment.html"


class DataView(View):
    tab = DATA


def _get(rf, view=View, **headers):
    request = rf.get("/tab/", headers=headers)
    request.htmx = HtmxDetails(request)
    return view.as_view()(request).content.decode().strip()


@pytest.fixture(autouse=True)
def _templates():
    with override_settings(TEMPLATES=TEMPLATES):
        yield


def test_a_plain_request_gets_the_page_around_the_tab(rf):
    content = _get(rf)

    assert content == "page Shop | Overview index=/index/ data=/data/ tab=index /index/"


def test_an_htmx_request_gets_the_fragment(rf):
    assert _get(rf, HX_Request="true") == "fragment tab=index /index/"


def test_an_htmx_history_restore_gets_the_whole_page(rf):
    content = _get(rf, HX_Request="true", HX_History_Restore_Request="true")

    assert content == "page Shop | Overview index=/index/ data=/data/ tab=index /index/"


@pytest.mark.parametrize(
    "view, expected",
    [(View, "tab=index /index/"), (DataView, "tab=data /data/")],
    ids=["default", "set"],
)
def test_a_view_without_a_tab_gets_the_default_one(rf, view, expected):
    assert _get(rf, view, HX_Request="true").endswith(expected)


def test_the_fragment_defaults_to_the_core_one(rf):
    content = _get(rf, Shop, HX_Request="true")

    assert "<title>Shop | Overview</title>" in content
    assert (
        '<div hx-get="/index/" hx-target="#tab_content" '
        'hx-trigger="reload from:body"></div>'
    ) in content
    assert content.endswith("tab=index /index/")
