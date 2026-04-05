import pytest

from ...services.model_services import CommonMethodsMixin


class DummyMixinService(CommonMethodsMixin):
    """A dummy class just to test the pure mixin methods."""

    pass


def test_common_methods_mixin_year_not_implemented():
    service = DummyMixinService()

    with pytest.raises(NotImplementedError, match="Method year is not implemented."):
        service.year(2026)


def test_common_methods_mixin_items_not_implemented():
    service = DummyMixinService()

    with pytest.raises(NotImplementedError, match="Method items is not implemented."):
        service.items()
