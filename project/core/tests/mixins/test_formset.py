from unittest.mock import Mock

import pytest

from ...mixins.formset import BaseOwnerFormSet, FormsetMixin
from ..utils import setup_view


class DummyTypesService:
    def __init__(self, user):
        self.user = user

    def items(self):
        return ["Account1", "Account2"]


class OnePensionService(DummyTypesService):
    def items(self):
        return ["P1"]


class NoItemsService(DummyTypesService):
    def items(self):
        return []


class StubFormsetView(FormsetMixin):
    pass


@pytest.mark.parametrize(
    "owner_service, owner_field, expect",
    [
        pytest.param(
            OnePensionService, "pension_type", [{"pension_type": "P1"}], id="one_item"
        ),
        pytest.param(NoItemsService, "account", [], id="no_items"),
        pytest.param(
            DummyTypesService,
            "account",
            [{"account": "Account1"}, {"account": "Account2"}],
            id="account",
        ),
        pytest.param(
            DummyTypesService,
            "saving_type",
            [{"saving_type": "Account1"}, {"saving_type": "Account2"}],
            id="saving_type",
        ),
    ],
)
def test_formset_initial_keys_each_item_by_the_service_models_owner_field(
    fake_request, owner_service, owner_field, expect
):
    service_instance = Mock()
    service_instance.objects.model = Mock(owner_field=owner_field)

    view = setup_view(StubFormsetView(), fake_request)
    view.owner_service_class = owner_service
    view.service_class = Mock(return_value=service_instance)

    assert view.formset_initial() == expect


def test_clean_without_an_owner_field_raises(mocker):
    mocker.patch.object(BaseOwnerFormSet, "__init__", return_value=None)
    mocker.patch.object(
        BaseOwnerFormSet, "errors", new_callable=mocker.PropertyMock, return_value=[]
    )
    formset = BaseOwnerFormSet()
    formset.model = mocker.Mock(spec=[])

    with pytest.raises(AttributeError, match="owner_field"):
        formset.clean()
