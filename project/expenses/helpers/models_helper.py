import os
from datetime import datetime


def upload_attachment(instance, filename):
    now = datetime.now()
    f = f'{now.year}.{now.strftime("%m")}_{filename}'

    return os.path.join(instance.expense_type.slug, f)
