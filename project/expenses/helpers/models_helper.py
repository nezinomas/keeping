import os
from datetime import datetime


def upload_attachment(instance, filename):
    now = datetime.now()

    if instance.pk:
        now = instance.date

    f = f'{now.year}.{now.strftime("%m")}_{filename}'

    journal = str(instance.expense_type.journal.pk)
    return os.path.join(journal, instance.expense_type.slug, f)
