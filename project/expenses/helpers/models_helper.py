from datetime import datetime
from pathlib import Path


def attachment_folder(expense_type):
    return Path(str(expense_type.journal_id)) / str(expense_type.pk)


def upload_attachment(instance, filename):
    now = datetime.now()

    if instance.pk:
        now = instance.date

    file = f"{now.year}.{now.strftime('%m')}_{filename}"

    return attachment_folder(instance.expense_type) / file
