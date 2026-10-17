from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from django.db.models import Max, QuerySet
from django.db.models.expressions import Combinable
from django.db.models.functions import Coalesce

from ...users.models import User

_QS = TypeVar("_QS")


class BaseModelService(ABC, Generic[_QS]):
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    @property
    def objects(self) -> _QS:
        """Returns a freshly constructed base queryset on every access."""
        return self.get_queryset()

    @abstractmethod
    def get_queryset(self) -> _QS: ...

    @abstractmethod
    def items(self) -> _QS: ...


class DatedModelService(BaseModelService[_QS]):
    @abstractmethod
    def year(self, year: int) -> _QS: ...


def max_year(*rows: tuple[QuerySet, Combinable]) -> int:
    """The latest year of (queryset, year expression) pairs, one query each; 0 when
    none has a row."""
    return max(qs.aggregate(year=Coalesce(Max(year), 0))["year"] for qs, year in rows)
