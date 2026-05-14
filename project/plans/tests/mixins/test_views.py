import pytest
from django.http import Http404
from django.utils.translation import gettext as _

from ...mixins.views import (
    CssClassMixin,
    PlanDeleteMixin,
    PlanQuerySetMixin,
    PlanUpdateMixin,
)

# -------------------------------------------------------------------------------------
#                                                                         CssClassMixin
# -------------------------------------------------------------------------------------


def test_css_class_mixin():
    class DummyView(CssClassMixin):
        pass

    assert DummyView().modal_body_css_class == "plans-form"


# -------------------------------------------------------------------------------------
#                                                                     PlanQuerySetMixin
# -------------------------------------------------------------------------------------


def test_plan_queryset_mixin(mocker):
    mock_queryset = mocker.Mock()
    mock_service_instance = mocker.Mock()
    mock_service_instance.items.return_value = mock_queryset

    mock_service_class = mocker.Mock(return_value=mock_service_instance)

    class DummyView(PlanQuerySetMixin):
        service_class = mock_service_class
        request = mocker.Mock(user="test_user")
        kwargs = {"year": 2026, "income_type_id": 5}

    view = DummyView()
    result = view.get_tall_queryset()

    mock_service_class.assert_called_once_with("test_user")
    mock_queryset.filter.assert_called_once_with(year=2026, income_type_id=5)

    assert result == mock_queryset.filter.return_value


# -------------------------------------------------------------------------------------
#                                                    PlanUpdateMixin & PlanDeleteMixin
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize("mixin", [PlanUpdateMixin, PlanDeleteMixin])
class TestObjectAndUrlMixins:
    def test_get_object_found(self, mocker, mixin):
        class DummyView(mixin):
            pass

        view = DummyView()

        # Mock queryset
        mocker.patch.object(view, "get_tall_queryset")
        view.get_tall_queryset.return_value.first.return_value = "my_dummy_plan"

        assert view.get_object() == "my_dummy_plan"

    def test_get_object_not_found(self, mocker, mixin):
        class DummyView(mixin):
            pass

        view = DummyView()

        mocker.patch.object(view, "get_tall_queryset")
        view.get_tall_queryset.return_value.first.return_value = None

        with pytest.raises(Http404, match=_("No plans found.")):
            view.get_object()

    def test_url_without_object(self, mixin):
        class DummyView(mixin):
            object = None

        view = DummyView()

        assert view.url() is None

    def test_url_with_object(self, mixin):
        class DummyView(mixin):
            object = "exists"
            url_name = "income_update"
            kwargs = {"year": 2026, "income_type_id": 5}

        view = DummyView()

        assert str(view.url()) == "/plans/incomes/update/2026/5/"


# -------------------------------------------------------------------------------------
#                                                                      PlanDeleteMixin
# -------------------------------------------------------------------------------------


def test_plan_delete_mixin_post(mocker):
    mock_super_post_response = mocker.Mock()

    class BaseView:
        def post(self, request, *args, **kwargs):
            return mock_super_post_response

    class DummyView(PlanDeleteMixin, BaseView):
        pass

    view = DummyView()

    mock_queryset = mocker.Mock()
    mocker.patch.object(view, "get_tall_queryset", return_value=mock_queryset)

    dummy_request = mocker.Mock()
    response = view.post(dummy_request, year=2026)

    mock_queryset.delete.assert_called_once()

    assert response == mock_super_post_response
