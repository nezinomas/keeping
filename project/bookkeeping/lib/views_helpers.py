from ...expenses.models import ExpenseType


def expense_types(*args):
    qs = list(ExpenseType.objects.all().values_list('title', flat=True))

    [qs.append(x) for x in args]

    qs.sort()

    return list(qs)
