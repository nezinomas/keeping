import os

from ..factories import ExpenseFactory
from ..helpers import models_helper as T


def test_upload_attachment():
    e = ExpenseFactory.build()
    f = 'x.jpg'

    actual = T.upload_attachment(e, f)

    assert actual == os.path.join(e.expense_type.slug, f)
