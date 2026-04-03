import pytest
from django.core.exceptions import ImproperlyConfigured

from ...mixins.queryset import GetQuerysetMixin


class DummyService:
    def __init__(self, user):
        self.user = user

    @property
    def objects(self):
        return f"data_for_{self.user.username}"


class TestView(GetQuerysetMixin):
    """A clean instance for us to inject properties into during tests."""

    pass


def test_missing_service_class_raises_improperly_configured():
    """If service_class is None, it must halt execution."""
    view = TestView()

    with pytest.raises(ImproperlyConfigured) as exc_info:
        view.get_queryset()

    assert (
        "[project.core.tests.mixins.test_queryset.TestView] is missing a data source."
        in str(exc_info.value)
    )


def test_service_class_is_not_callable(mocker):
    """If a developer accidentally sets service_class to a string or instance, it should fail."""
    view = TestView()
    view.service_class = "IncomeModelService"
    view.request = mocker.Mock()

    with pytest.raises(TypeError):
        # Trying to instantiate a string will raise a TypeError
        view.get_queryset()


def test_missing_request_object_crashes_predictably():
    """
    In Django, .setup() attaches the request to the View.
    If get_queryset is called too early, it should raise an AttributeError.
    """
    view = TestView()
    view.service_class = DummyService

    with pytest.raises(AttributeError) as exc_info:
        view.get_queryset()

    assert "has no attribute 'request'" in str(exc_info.value)


def test_missing_user_on_request_crashes_predictably(mocker):
    """If the authentication middleware fails and request.user is missing, it must crash."""
    view = TestView()
    view.service_class = DummyService

    # Create a request but delete the user attribute
    mock_request = mocker.Mock(spec=[])
    view.request = mock_request

    with pytest.raises(AttributeError) as exc_info:
        view.get_queryset()

    assert "has no attribute 'user'" in str(exc_info.value)


def test_get_queryset_returns_secure_service_objects(mocker):
    """It must successfully instantiate the service and return the objects property."""
    view = TestView()
    view.service_class = DummyService

    mock_request = mocker.Mock()
    mock_request.user.username = "admin"
    view.request = mock_request

    actual = view.get_queryset()

    assert actual == "data_for_admin"


def test_service_is_instantiated_with_exact_user(mocker):
    """
    SPY TEST: We must prove that the mixin explicitly passes `request.user`
    into the service, and nothing else.
    """
    view = TestView()

    SpyServiceClass = mocker.Mock()
    view.service_class = SpyServiceClass

    mock_request = mocker.Mock()
    view.request = mock_request

    view.get_queryset()

    # Service MUST have been called exactly once,
    # and exactly with the request.user object.
    SpyServiceClass.assert_called_once_with(mock_request.user)
