from ...services.model_services import CommonMethodsMixin


def test_common_methods_mixin_promises_no_year():
    assert not hasattr(CommonMethodsMixin, "year")
