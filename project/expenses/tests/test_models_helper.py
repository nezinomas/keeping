from datetime import date
from pathlib import Path

import pytest
from django.core.files import File
from mock import MagicMock
from override_storage import override_storage

from ..factories import ExpenseFactory
from ..helpers import models_helper as helper

pytestmark = pytest.mark.django_db


def test_upload_attachment(main_user):
    e = ExpenseFactory(date=date(1000, 1, 1))
    f = "x.jpg"

    actual = helper.upload_attachment(e, f)

    assert (
        actual
        == Path(str(main_user.journal.pk)) / e.expense_type.slug / "1000.01_x.jpg"
    )


@override_storage()
@pytest.mark.django_db
def test_upload_attachment_on_update(main_user):
    e = ExpenseFactory()

    file_mock = MagicMock(spec=File, name="FileMock")
    file_mock.name = "x.jpg"

    e.attachment = file_mock

    e.save()

    assert e.attachment.name == f"{main_user.journal.pk}/expense-type/1999.01_x.jpg"
