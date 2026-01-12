from typing import Any, cast
from django.db.models import Model

from ...users.models import User
from ...core.services.model_services import BaseModelService


class ModelService(BaseModelService):
    def __init__(self, model: Model, user: User):
        self.model_cls = model

        super().__init__(user)

    def get_queryset(self):
        return cast(Any, self.model_cls.objects).related(self.user)

    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects
