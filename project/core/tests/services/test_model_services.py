import pytest

from ...services.model_services import DatedModelService


class DatedWithoutYear(DatedModelService):
    def get_queryset(self):
        return []

    def items(self):
        return []


def test_a_dated_service_must_say_how_it_reads_a_year(main_user):
    with pytest.raises(TypeError, match="year"):
        DatedWithoutYear(main_user)
