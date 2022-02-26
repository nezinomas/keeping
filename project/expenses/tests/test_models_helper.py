import os
from datetime import date

import pytest
from django.core.files import File
from mock import MagicMock
from override_storage import override_storage

from ..factories import ExpenseFactory
from ..helpers import models_helper as T

pytestmark = pytest.mark.django_db



def test_upload_attachment(get_user):
    e = ExpenseFactory(date=date(1000, 1, 1))
    f = 'x.jpg'

    actual = T.upload_attachment(e, f)

    assert actual == os.path.join(str(get_user.journal.pk), e.expense_type.slug, '1000.01_x.jpg')


@override_storage()
@pytest.mark.django_db
def test_upload_attachment_on_update(get_user):
    e = ExpenseFactory()

    file_mock = MagicMock(spec=File, name='FileMock')
    file_mock.name = 'x.jpg'

    e.attachment=file_mock

    e.save()

    assert e.attachment.name == f'{get_user.journal.pk}/expense-type/1999.01_x.jpg'
