from datetime import datetime
from pathlib import Path

# the storage appends "_" and 7 random characters to a name that is already taken
TAKEN_NAME_SUFFIX_LENGTH = 8


def attachment_folder(expense_type):
    return Path(str(expense_type.journal_id)) / str(expense_type.pk)


def upload_attachment(instance, filename):
    now = datetime.now()

    if instance.pk:
        now = instance.date

    max_length = instance._meta.get_field("attachment").max_length
    prefix = f"{now.year}.{now.strftime('%m')}_"
    folder = attachment_folder(instance.expense_type)
    room = max_length - TAKEN_NAME_SUFFIX_LENGTH - len(str(folder / prefix))

    name = filename
    if len(name) > room:
        suffix = Path(name).suffix
        name = Path(name).stem[: max(room - len(suffix), 0)] + suffix

    return folder / f"{prefix}{name}"
