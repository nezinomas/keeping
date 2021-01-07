import os

def upload_attachment(instance, filename):
    return os.path.join(instance.expense_type.slug, filename)
