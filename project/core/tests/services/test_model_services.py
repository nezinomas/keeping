import pytest

from ...services.model_services import BaseModelService, DatedModelService


class Undated(BaseModelService):
    def get_queryset(self):
        return []

    def items(self):
        return []


class DatedWithoutYear(DatedModelService):
    def get_queryset(self):
        return []

    def items(self):
        return []


def test_a_dated_service_must_say_how_it_reads_a_year(main_user):
    with pytest.raises(TypeError, match="year"):
        DatedWithoutYear(main_user)


def test_an_undated_service_is_not_asked_for_a_year(main_user):
    assert Undated(main_user).items() == []
