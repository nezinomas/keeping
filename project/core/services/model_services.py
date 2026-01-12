from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ...users.models import User

_QS = TypeVar("_QS")


class BaseModelService(ABC, Generic[_QS]):
    objects: _QS

    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.objects = self.get_queryset()

    @abstractmethod
    def get_queryset(self) -> _QS: ...

    @abstractmethod
    def year(self, year: int): ...

    @abstractmethod
    def items(self): ...
