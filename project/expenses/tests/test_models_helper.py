import os

from freezegun import freeze_time

from ..factories import ExpenseFactory
from ..helpers import models_helper as T

@freeze_time('1000-1-1')
def test_upload_attachment():
    e = ExpenseFactory.build()
    f = 'x.jpg'

    actual = T.upload_attachment(e, f)

    assert actual == os.path.join(e.expense_type.slug, '1000.01_x.jpg')
