from datetime import datetime
from pathlib import Path


def upload_attachment(instance, filename):
    now = datetime.now()

    if instance.pk:
        now = instance.date

    journal = str(instance.expense_type.journal.pk)
    expense_type = instance.expense_type.slug
    file = f'{now.year}.{now.strftime("%m")}_{filename}'

    return Path(journal) / expense_type / file
