from .models import Debt


class DebtTypeConverter:
    regex = "|".join(Debt.DebtType.values)

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
