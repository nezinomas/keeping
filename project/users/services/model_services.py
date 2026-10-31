from ...core.services.model_services import BaseModelService
from .. import models


class UserModelService(BaseModelService):
    def get_queryset(self):
        return models.User.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def items(self):
        raise NotImplementedError("Method items is not implemented.")
