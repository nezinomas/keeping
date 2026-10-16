from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLResolver, get_resolver
from django.utils.module_loading import import_string
from vanilla import CreateView

from ...mixins.formset import FormsetMixin
from ...mixins.queryset import GetQuerysetMixin


class DummyService:
    def __init__(self, user):
        self.user = user

    @property
    def objects(self):
        return f"data_for_{self.user.username}"


class QuerysetView(GetQuerysetMixin):
    pass


def test_missing_service_class_raises_improperly_configured():
    view = QuerysetView()

    with pytest.raises(ImproperlyConfigured) as exc_info:
        view.get_queryset()

    assert (
        "[project.core.tests.mixins.test_queryset.QuerysetView] is missing a data source."
        in str(exc_info.value)
    )


def test_service_class_is_not_callable(mocker):
    view = QuerysetView()
    view.service_class = "IncomeModelService"
    view.request = mocker.Mock()

    with pytest.raises(TypeError):
        view.get_queryset()


@pytest.mark.parametrize(
    "attrs, missing",
    [
        pytest.param({}, "request", id="no_request"),
        pytest.param({"request": SimpleNamespace()}, "user", id="no_user"),
    ],
)
def test_get_queryset_without_request_user_raises(attrs, missing):
    view = QuerysetView()
    view.service_class = DummyService
    vars(view).update(attrs)

    with pytest.raises(AttributeError) as exc_info:
        view.get_queryset()

    assert f"has no attribute '{missing}'" in str(exc_info.value)


def test_get_queryset_returns_secure_service_objects(mocker):
    view = QuerysetView()
    view.service_class = DummyService

    mock_request = mocker.Mock()
    mock_request.user.username = "admin"
    view.request = mock_request

    actual = view.get_queryset()

    assert actual == "data_for_admin"


def _view_classes(patterns):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _view_classes(pattern.url_patterns)
            continue

        if view_class := getattr(pattern.callback, "view_class", False):
            yield view_class


def _get_queryset_reads(view):
    # a CreateView never calls get_queryset
    return view.get_queryset is GetQuerysetMixin.get_queryset and not issubclass(
        view, CreateView
    )


# A view's service_class is read when one of these holds for it.
SERVICE_CLASS_READERS = {
    "GetQuerysetMixin.get_queryset": _get_queryset_reads,
    "FormsetMixin": lambda view: issubclass(view, FormsetMixin),
    # by path: core's tests import no app
    "PlanQuerySetMixin": lambda view: issubclass(
        view, import_string("project.plans.mixins.views.PlanQuerySetMixin")
    ),
}


def _sets_service_class(view):
    return any(
        "service_class" in vars(cls)
        for cls in view.__mro__
        if cls is not GetQuerysetMixin
    )


def test_a_view_sets_service_class_only_where_it_is_read():
    views = set(_view_classes(get_resolver().url_patterns))

    unread = sorted(
        f"{view.__module__}.{view.__qualname__}"
        for view in views
        if _sets_service_class(view)
        and not any(reads(view) for reads in SERVICE_CLASS_READERS.values())
    )

    assert not unread, "service_class read by nothing:\n" + "\n".join(unread)
