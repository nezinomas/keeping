from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from mock import Mock

from ...mixins.formset import FormsetMixin
from ..utils import setup_view


def test_model_type_without_foreignkey(fake_request):
    mock_model_class = Mock()
    mock_model_class._meta.get_fields.return_value = [
        SimpleNamespace(name="F", many_to_one=False)
    ]

    mock_service_instance = Mock()
    mock_service_instance.objects.model = mock_model_class

    mock_service_class = Mock(return_value=mock_service_instance)

    class Dummy(FormsetMixin):
        category_service_class = None
        service_class = mock_service_class

    view = setup_view(Dummy(), fake_request)

    actual = view.formset_initial()

    assert not actual 


# ==========================================
# 1. Dummy Framework Setup
# ==========================================


class DummyField:
    """Mocks Django's model field for the _meta introspection test."""

    def __init__(self, name, many_to_one):
        self.name = name
        self.many_to_one = many_to_one


class DummyMeta:
    """Mocks Django's Model._meta"""

    def __init__(self, fields):
        self._fields = fields

    def get_fields(self):
        return self._fields


class DummyModel:
    """Mocks a Django Database Model"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyQuerySet:
    """Mocks a service.objects queryset"""

    model = DummyModel

    def bulk_create(self, objects):
        pass


class DummyService:
    def __init__(self, user):
        self.user = user
        self.objects = DummyQuerySet()


class DummyTypesService:
    def __init__(self, user):
        self.user = user

    def items(self):
        return ["Account1", "Account2"]


class DummyBaseView:
    """Mocks the super() calls expected by the mixin."""

    def form_invalid(self, formset):
        return "mocked_form_invalid_response"

    def get_context_data(self, **kwargs):
        return {"base_context": True}


class TestView(FormsetMixin, DummyBaseView):
    """A clean instance of our mixin hooked to a dummy base view."""

    def get_formset_class(self):
        return "MockedFormClass"

    def get_hx_trigger_django(self):
        return "hx-refresh-trigger"


# ==========================================
# 2. PROPERTY TESTS (Configuration)
# ==========================================


def test_missing_service_class_raises_error(mocker):
    """If a developer forgets service_class, the property should crash loudly."""
    view = TestView()
    view.request = mocker.Mock()

    with pytest.raises(ImproperlyConfigured) as exc_info:
        _ = view.service_instance

    assert "missing a data source" in str(exc_info.value)


def test_lazy_properties_instantiate_correctly(mocker):
    """Proves the service is instantiated exactly once, with the correct user."""
    view = TestView()
    view.service_class = mocker.Mock(return_value=DummyService(user="test_user"))
    view.request = mocker.Mock()
    view.request.user = "test_user"

    # Trigger the property
    instance = view.service_instance
    model = view.model_class

    # Assertions
    view.service_class.assert_called_once_with("test_user")
    assert model == DummyModel


# ==========================================
# 3. FORMSET_INITIAL TESTS (Introspection)
# ==========================================


def test_formset_initial_returns_empty_if_no_foreign_key(mocker):
    """If the target model has no foreign keys, it should safely return an empty list."""
    view = TestView()
    view.category_service_class = DummyTypesService

    # Mock the model to have ONLY a price field, no foreign keys
    mocker.patch.object(TestView, "model_class", create=True)
    view.model_class._meta = DummyMeta([DummyField("price", False)])

    actual = view.formset_initial()
    assert actual == []


def test_formset_initial_populates_via_category_service_class(mocker):
    """If foreign keys exist, it should ask category_service_class for items and build the list."""
    view = TestView()
    view.category_service_class = DummyTypesService
    view.request = mocker.Mock()

    # Mock the model to have a foreign key named 'account'
    mocker.patch.object(TestView, "model_class", create=True)
    view.model_class._meta = DummyMeta([DummyField("account", True)])

    actual = view.formset_initial()

    # Expecting 2 dictionaries because DummyTypesService returns 2 accounts
    assert len(actual) == 2
    assert actual[0] == {"price": None, "account": "Account1"}
    assert actual[1] == {"price": None, "account": "Account2"}


# ==========================================
# 4. GET_FORMSET TESTS (Factory Logic)
# ==========================================


def test_get_formset_for_get_request(mocker):
    """A GET request (post=None) should initialize the formset with formset_initial()."""
    view = TestView()
    mocker.patch.object(TestView, "model_class", create=True)
    mocker.patch.object(TestView, "formset_initial", return_value=[{"initial": "data"}])

    # Mock the factory and the resulting formset class
    mock_formset_class = mocker.Mock()
    mock_factory = mocker.patch(
        "project.core.mixins.formset.modelformset_factory",
        return_value=mock_formset_class,
    )

    # Call it
    view.get_formset(post=None)

    # Prove it injected the initial data
    mock_formset_class.assert_called_once_with(initial=[{"initial": "data"}])


def test_get_formset_for_post_request(mocker):
    """A POST request should pass the POST data and IGNORE formset_initial()."""
    view = TestView()
    mocker.patch.object(TestView, "model_class", create=True)
    mock_formset_initial = mocker.patch.object(TestView, "formset_initial")

    mock_formset_class = mocker.Mock()
    mocker.patch(
        "project.core.mixins.formset.modelformset_factory",
        return_value=mock_formset_class,
    )

    post_data = {"form-TOTAL_FORMS": 2}
    view.get_formset(post=post_data)

    # Prove it passed the POST data and did NOT call initial
    mock_formset_class.assert_called_once_with(post_data)
    mock_formset_initial.assert_not_called()


# ==========================================
# 5. POST & SAVE TESTS (The Business Logic)
# ==========================================


def test_post_with_invalid_formset(mocker):
    """If the formset fails validation, it must halt and return form_invalid()."""
    view = TestView()
    mock_request = mocker.Mock()

    # Create a mock formset that is invalid
    mock_formset = mocker.Mock()
    mock_formset.is_valid.return_value = False
    mocker.patch.object(TestView, "get_formset", return_value=mock_formset)

    response = view.post(mock_request)

    assert response == "mocked_form_invalid_response"


def test_post_skips_empty_prices_and_does_not_save(mocker):
    """If the user submits valid forms but leaves all prices empty, it shouldn't hit the DB."""
    view = TestView()

    mock_form1 = mocker.Mock(cleaned_data={"price": None})
    mock_form2 = mocker.Mock(cleaned_data={})  # price key missing completely

    mock_formset = mocker.Mock()
    mock_formset.is_valid.return_value = True
    mock_formset.__iter__ = mocker.Mock(return_value=iter([mock_form1, mock_form2]))

    mocker.patch.object(TestView, "get_formset", return_value=mock_formset)
    mocker.patch.object(TestView, "model_class", create=True)
    mocker.patch(
        "project.core.mixins.formset.http_htmx_response", return_value="hx_success"
    )

    mock_bulk_create = mocker.patch.object(DummyQuerySet, "bulk_create")
    view.service_class = mocker.Mock(return_value=DummyService("user"))

    response = view.post(mocker.Mock())

    # Prove bulk create was never fired because no valid prices existed
    mock_bulk_create.assert_not_called()
    assert response == "hx_success"


def test_post_saves_valid_prices_and_triggers_signals(mocker):
    """If prices exist, it must instantiate objects, bulk create them, and fire signals."""
    view = TestView()
    mock_request = mocker.Mock()
    view.request = mock_request

    # Two forms: One valid, one empty. It should only save the valid one.
    mock_form1 = mocker.Mock(cleaned_data={"price": 100, "account": "A1"})
    mock_form2 = mocker.Mock(cleaned_data={"price": None, "account": "A2"})

    mock_formset = mocker.Mock()
    mock_formset.is_valid.return_value = True
    mock_formset.__iter__ = mocker.Mock(return_value=iter([mock_form1, mock_form2]))

    mocker.patch.object(TestView, "get_formset", return_value=mock_formset)
    mocker.patch(
        "project.core.mixins.formset.http_htmx_response", return_value="hx_success"
    )

    # Set up our dummy service to intercept bulk_create
    dummy_service = DummyService("user")
    mock_bulk_create = mocker.patch.object(dummy_service.objects, "bulk_create")
    view.service_class = mocker.Mock(return_value=dummy_service)

    # Mock the Signals dictionary
    mock_signal = mocker.Mock()
    mock_signals_dict = {DummyModel: mock_signal}
    mocker.patch("project.core.mixins.formset.SIGNALS", mock_signals_dict)

    # Execute
    view.post(mocker.Mock())

    # 1. Prove bulk_create was called exactly once, with exactly one object (form1)
    assert mock_bulk_create.call_count == 1
    created_objects_list = mock_bulk_create.call_args[0][0]
    assert len(created_objects_list) == 1
    assert isinstance(created_objects_list[0], DummyModel)
    assert created_objects_list[0].kwargs == {"price": 100, "account": "A1"}

    # 2. Prove the signal was fired with the correct sender and instance
    mock_signal.assert_called_once_with(
        sender=DummyModel, instance=created_objects_list[0]
    )


# ==========================================
# 6. CONTEXT DATA TESTS
# ==========================================


def test_get_context_data_injects_variables(mocker):
    """It must preserve super() context and inject formset variables."""
    view = TestView()
    view.request = mocker.Mock()
    view.modal_form_title = "My Custom Title"

    mocker.patch.object(TestView, "get_formset", return_value="injected_formset")

    actual = view.get_context_data()

    assert actual["base_context"] is True
    assert actual["formset"] == "injected_formset"
    assert actual["modal_form_title"] == "My Custom Title"
    assert actual["modal_body_css_class"] == "worth-form"  # Default fallback
