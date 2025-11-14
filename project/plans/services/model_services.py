from django.db.models import Model

from ...users.models import User


class ModelService:
    def __init__(self, model: Model, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = model.objects.related(user)

    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects
