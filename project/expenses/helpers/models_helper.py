import os
from datetime import datetime


def upload_attachment(instance, filename):
    now = datetime.now()

    if instance.pk:
        now = instance.date

    f = f'{now.year}.{now.strftime("%m")}_{filename}'

    return os.path.join(instance.expense_type.slug, f)
