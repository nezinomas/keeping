from datetime import date
from pathlib import Path

import pytest
import time_machine
from django.core.files.base import ContentFile
from override_storage import override_storage

from ...helpers import models_helper as helper
from ...models import Expense
from ..factories import ExpenseFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db

MAX_LENGTH = Expense._meta.get_field("attachment").max_length


@pytest.mark.parametrize(
    ("saved", "month"),
    [(False, "1974.03"), (True, "1000.01")],
    ids=["new_is_filed_under_today", "saved_keeps_its_expense_date"],
)
def test_upload_attachment(main_user, saved, month):
    e = ExpenseFactory.build(expense_type=ExpenseTypeFactory())
    if saved:
        e = ExpenseFactory(date=date(1000, 1, 1))

    with time_machine.travel("1974-3-7"):
        actual = helper.upload_attachment(e, "x.jpg")

    assert (
        actual
        == Path(str(main_user.journal.pk)) / str(e.expense_type.pk) / f"{month}_x.jpg"
    )


@override_storage()
@time_machine.travel("1974-1-1")
def test_a_long_upload_name_is_shortened_to_fit_the_column(main_user):
    name = "a" * (MAX_LENGTH - 5) + ".jpg"

    expense = ExpenseFactory(attachment=ContentFile(b"x", name=name))

    stored = expense.attachment.name
    folder = f"{main_user.journal.pk}/{expense.expense_type.pk}"
    assert len(stored) <= MAX_LENGTH
    assert stored.startswith(f"{folder}/1974.01_aaa")
    assert stored.endswith("a.jpg")


@override_storage()
@time_machine.travel("1974-1-1")
def test_a_long_upload_name_taken_twice_still_fits_the_column(main_user):
    name = "a" * (MAX_LENGTH - 5) + ".jpg"

    first = ExpenseFactory(attachment=ContentFile(b"x", name=name))
    second = ExpenseFactory(attachment=ContentFile(b"y", name=name))

    assert first.attachment.name != second.attachment.name
    assert len(second.attachment.name) <= MAX_LENGTH
