import pytest

from ...services.model_services import CommonMethodsMixin


class DummyMixinService(CommonMethodsMixin):
    """A dummy class just to test the pure mixin methods."""

    pass


def test_common_methods_mixin_items_not_implemented():
    service = DummyMixinService()

    with pytest.raises(NotImplementedError, match="Method items is not implemented."):
        service.items()


def test_common_methods_mixin_promises_no_year():
    assert not hasattr(CommonMethodsMixin, "year")
