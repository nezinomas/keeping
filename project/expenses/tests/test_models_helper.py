import os

import pytest
from django.core.files import File
from freezegun import freeze_time
from mock import MagicMock
from override_storage import override_storage

from ..factories import ExpenseFactory
from ..helpers import models_helper as T


@freeze_time('1000-1-1')
def test_upload_attachment():
    e = ExpenseFactory.build()
    f = 'x.jpg'

    actual = T.upload_attachment(e, f)

    assert actual == os.path.join(e.expense_type.slug, '1000.01_x.jpg')


@override_storage()
@pytest.mark.django_db
def test_upload_attachment_on_update():
    e = ExpenseFactory()

    file_mock = MagicMock(spec=File, name='FileMock')
    file_mock.name = 'x.jpg'

    e.attachment=file_mock

    e.save()

    assert e.attachment.name == os.path.join('expense-type', '1999.01_x.jpg')
