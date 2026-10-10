from datetime import date
from io import StringIO
from pathlib import Path

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.db import connection
from django.db.models import QuerySet
from django.test.utils import CaptureQueriesContext

from ..models import Expense
from .factories import ExpenseFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def _legacy(media, folder, name="1999.01_x.jpg", *, on_disk=True, **kwargs):
    expense = ExpenseFactory(**kwargs)
    stored = f"{expense.expense_type.journal_id}/{folder}/{name}"
    Expense.objects.filter(pk=expense.pk).update(attachment=stored)
    if on_disk:
        path = media / stored
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    return expense


def _pk_folder(expense):
    return f"{expense.expense_type.journal_id}/{expense.expense_type.pk}"


def _run(*args):
    out = StringIO()
    call_command("move_attachments", *args, stdout=out)
    return out.getvalue().splitlines()


def _stored(expense):
    return Expense.objects.get(pk=expense.pk).attachment.name


def test_moves_into_pk_folder(media):
    e = _legacy(media, "expense-type")
    old = f"{e.expense_type.journal_id}/expense-type/1999.01_x.jpg"
    new = f"{_pk_folder(e)}/1999.01_x.jpg"

    lines = _run()

    assert lines == [f"{old} -> {new}", "moved 1, missing 0"]
    assert _stored(e) == new
    assert (media / new).read_bytes() == b"1999.01_x.jpg"
    assert not (media / old).exists()


def test_taken_name_takes_the_storage_suffix(media):
    e = _legacy(media, "expense-type")
    taken = media / _pk_folder(e) / "1999.01_x.jpg"
    taken.parent.mkdir(parents=True)
    taken.write_bytes(b"other")

    _run()

    stored = _stored(e)
    assert stored != f"{_pk_folder(e)}/1999.01_x.jpg"
    assert stored.startswith(f"{_pk_folder(e)}/")
    assert (media / stored).read_bytes() == b"1999.01_x.jpg"
    assert taken.read_bytes() == b"other"


def test_in_place_is_untouched_and_not_counted(media):
    e = ExpenseFactory()
    stored = f"{_pk_folder(e)}/1999.01_x.jpg"
    Expense.objects.filter(pk=e.pk).update(attachment=stored)
    path = media / stored
    path.parent.mkdir(parents=True)
    path.write_bytes(b"keep")

    lines = _run()

    assert lines == ["moved 0, missing 0"]
    assert _stored(e) == stored
    assert path.read_bytes() == b"keep"


def test_row_without_attachment_is_ignored(media):
    ExpenseFactory()

    assert _run() == ["moved 0, missing 0"]


def test_missing_file_is_listed_and_row_kept(media):
    e = _legacy(media, "expense-type", on_disk=False)
    old = f"{e.expense_type.journal_id}/expense-type/1999.01_x.jpg"

    lines = _run()

    assert lines == [f"missing: {old}", "moved 0, missing 1"]
    assert _stored(e) == old


@pytest.mark.parametrize(
    ("stray", "folder_stays"),
    [(False, False), (True, True)],
)
def test_old_folder_goes_only_when_emptied(media, stray, folder_stays):
    e = _legacy(media, "expense-type")
    old_folder = media / str(e.expense_type.journal_id) / "expense-type"
    if stray:
        (old_folder / "no-row.jpg").write_bytes(b"x")

    lines = _run()

    assert old_folder.exists() is folder_stays
    assert (media / str(e.expense_type.journal_id)).exists()
    assert lines[-1] == "moved 1, missing 0"
    assert not any(line.startswith("not removed:") for line in lines)


@pytest.mark.parametrize(
    ("owner", "method", "refused"),
    [
        (Path, "rmdir", "not removed: {journal}/expense-type"),
        (
            FileSystemStorage,
            "delete",
            "not deleted: {journal}/expense-type/1999.01_x.jpg",
        ),
    ],
)
def test_what_the_os_refuses_is_listed_and_the_run_finishes(
    media, monkeypatch, owner, method, refused
):
    e = _legacy(media, "expense-type")

    def refuse(*args):
        raise PermissionError(13, "Access is denied")

    monkeypatch.setattr(owner, method, refuse)
    lines = _run()

    assert lines[-2:] == [
        refused.format(journal=e.expense_type.journal_id) + " (Access is denied)",
        "moved 1, missing 0",
    ]
    assert _stored(e) == f"{_pk_folder(e)}/1999.01_x.jpg"


def test_dry_run_changes_nothing(media):
    moved = _legacy(media, "expense-type")
    gone = _legacy(media, "other", on_disk=False, date=date(1999, 2, 1))
    old = f"{moved.expense_type.journal_id}/expense-type/1999.01_x.jpg"
    new = f"{_pk_folder(moved)}/1999.01_x.jpg"
    before = sorted(p.relative_to(media) for p in Path(media).rglob("*"))

    lines = _run("--dry-run")

    assert lines == [
        f"{old} -> {new}",
        f"missing: {gone.expense_type.journal_id}/other/1999.01_x.jpg",
        "dry run: moved 1, missing 1",
    ]
    assert _stored(moved) == old
    assert before == sorted(p.relative_to(media) for p in Path(media).rglob("*"))


def test_query_count_does_not_grow_with_rows(media):
    def queries(count):
        for i in range(count):
            _legacy(media, "expense-type", f"1999.01_{count}_{i}.jpg")
        with CaptureQueriesContext(connection) as ctx:
            _run()
        return len(ctx)

    assert queries(2) == queries(6)


@pytest.mark.parametrize("other_type", [False, True])
def test_rows_sharing_a_file_each_get_a_copy_per_type(media, other_type):
    first = _legacy(media, "expense-type")
    kwargs = {}
    if other_type:
        kwargs["expense_type"] = ExpenseTypeFactory(
            title="Other", journal=first.expense_type.journal
        )
    second = _legacy(media, "expense-type", **kwargs)
    old = media / str(first.expense_type.journal_id) / "expense-type"

    lines = _run()

    for expense in (first, second):
        stored = _stored(expense)
        assert stored == f"{_pk_folder(expense)}/1999.01_x.jpg"
        assert (media / stored).read_bytes() == b"1999.01_x.jpg"
        assert [p.name for p in (media / _pk_folder(expense)).iterdir()] == [
            "1999.01_x.jpg"
        ]
    assert lines[-1] == "moved 2, missing 0"
    assert not old.exists()


def test_a_file_a_row_in_place_still_uses_stays(media):
    kept = ExpenseFactory()
    folder = str(kept.expense_type.pk)
    kept = _legacy(media, folder, expense_type=kept.expense_type)
    retyped = _legacy(
        media,
        folder,
        expense_type=ExpenseTypeFactory(
            title="Other", journal=kept.expense_type.journal
        ),
    )

    _run()

    assert (media / _stored(kept)).read_bytes() == b"1999.01_x.jpg"
    assert (media / _stored(retyped)).read_bytes() == b"1999.01_x.jpg"


def test_a_failed_write_leaves_every_row_on_an_existing_file(media, monkeypatch):
    rows = [_legacy(media, "expense-type", f"1999.01_{i}.jpg") for i in range(2)]

    def boom(*args, **kwargs):
        raise RuntimeError

    monkeypatch.setattr(QuerySet, "bulk_update", boom)
    with pytest.raises(RuntimeError):
        _run()

    for expense in rows:
        assert (media / _stored(expense)).exists()
