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


@pytest.mark.parametrize(
    "content, named_by_a_row",
    [(b"other", False), (b"1999.01_x.jpg", True)],
)
def test_taken_name_takes_the_next_number(media, content, named_by_a_row):
    e = _legacy(media, "expense-type")
    taken = media / _pk_folder(e) / "1999.01_x.jpg"
    taken.parent.mkdir(parents=True)
    taken.write_bytes(content)
    if named_by_a_row:
        in_place = ExpenseFactory(expense_type=e.expense_type)
        Expense.objects.filter(pk=in_place.pk).update(
            attachment=f"{_pk_folder(e)}/1999.01_x.jpg"
        )

    _run()

    stored = _stored(e)
    assert stored == f"{_pk_folder(e)}/1999.01_x_2.jpg"
    assert (media / stored).read_bytes() == b"1999.01_x.jpg"
    assert taken.read_bytes() == content


def _same_basename_to_one_folder(media):
    first = _legacy(media, "a")
    second = _legacy(media, "b", expense_type=first.expense_type)
    (media / _stored(second)).write_bytes(b"second")
    return first, second


def test_dry_run_reports_the_targets_the_run_uses(media):
    _same_basename_to_one_folder(media)

    planned = _run("--dry-run")
    done = _run()

    assert planned[:-1] == done[:-1]
    assert planned[1].endswith("/1999.01_x_2.jpg")
    assert planned[-1] == "dry run: " + done[-1]


def test_a_rerun_after_a_crash_reuses_the_copies(media, monkeypatch):
    rows = _same_basename_to_one_folder(media)
    with monkeypatch.context() as patch:
        patch.setattr(QuerySet, "bulk_update", lambda *args, **kwargs: 1 / 0)
        with pytest.raises(ZeroDivisionError):
            _run()

    _run()

    folder = media / _pk_folder(rows[0])
    assert sorted(p.name for p in folder.iterdir()) == [
        "1999.01_x.jpg",
        "1999.01_x_2.jpg",
    ]
    assert [(media / _stored(e)).read_bytes() for e in rows] == [
        b"1999.01_x.jpg",
        b"second",
    ]


def test_an_old_file_in_a_pk_folder_is_not_taken_for_a_copy(media):
    expense_type = ExpenseTypeFactory()
    other = ExpenseTypeFactory(title="Other", journal=expense_type.journal)
    misfiled = _legacy(media, str(expense_type.pk), expense_type=other)
    legacy = _legacy(media, "expense-type", expense_type=expense_type)

    _run()

    for expense in (misfiled, legacy):
        assert (media / _stored(expense)).read_bytes() == b"1999.01_x.jpg"
    assert _stored(legacy) == f"{_pk_folder(legacy)}/1999.01_x_2.jpg"


@pytest.mark.parametrize(
    "name", ["1999.01_y.jpg", "1999.01_x.jpg"], ids=["own file", "shared file"]
)
def test_a_copy_the_os_refuses_is_listed_and_the_rest_moves(media, monkeypatch, name):
    refused = _legacy(media, "expense-type")
    other = ExpenseTypeFactory(title="Other", journal=refused.expense_type.journal)
    moved = _legacy(media, "expense-type", name, expense_type=other)
    old = _stored(refused)
    save = FileSystemStorage._save

    def full(storage, target, content):
        if target.startswith(f"{_pk_folder(refused)}/"):
            half = media / target
            half.parent.mkdir(parents=True, exist_ok=True)
            half.write_bytes(b"half")
            raise OSError("No space left on device")
        return save(storage, target, content)

    monkeypatch.setattr(FileSystemStorage, "_save", full)
    lines = _run()

    assert f"not copied: {old} (No space left on device)" in lines
    assert lines[-1] == "moved 1, missing 0"
    assert _stored(refused) == old
    assert (media / old).read_bytes() == b"1999.01_x.jpg"
    assert list((media / _pk_folder(refused)).iterdir()) == []
    assert _stored(moved) == f"{_pk_folder(moved)}/{name}"


def _full_length(expense_type):
    # the stored path fills the column, so the pk folder's name plus a suffix cannot
    prefix = f"{expense_type.journal_id}/ab/"
    max_length = Expense._meta.get_field("attachment").max_length
    return f"1999.01_{'x' * (max_length - len(prefix) - 12)}.jpg"


@pytest.mark.parametrize(
    "args, total",
    [((), "moved 0, missing 0"), (("--dry-run",), "dry run: moved 0, missing 0")],
)
def test_a_taken_name_too_long_for_a_suffix_is_listed_and_left(media, args, total):
    expense_type = ExpenseTypeFactory()
    name = _full_length(expense_type)
    e = _legacy(media, "ab", name, expense_type=expense_type)
    old = _stored(e)
    (media / _pk_folder(e)).mkdir(parents=True)
    (media / _pk_folder(e) / name).write_bytes(b"other")

    lines = _run(*args)

    assert len(old) == Expense._meta.get_field("attachment").max_length
    assert lines == [f"not moved: {old} (name too long)", total]
    assert _stored(e) == old
    assert (media / old).read_bytes() == name.encode()


def test_a_file_a_too_long_row_still_names_stays(media):
    expense_type = ExpenseTypeFactory()
    name = _full_length(expense_type)
    left = _legacy(media, "ab", name, expense_type=expense_type)
    moved = _legacy(
        media,
        "ab",
        name,
        expense_type=ExpenseTypeFactory(title="Other", journal=expense_type.journal),
    )
    (media / _pk_folder(left)).mkdir(parents=True)
    (media / _pk_folder(left) / name).write_bytes(b"other")

    _run()

    assert (media / _stored(left)).read_bytes() == name.encode()
    assert (media / _stored(moved)).read_bytes() == name.encode()


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
@pytest.mark.parametrize(
    "error",
    [PermissionError(13, "Access is denied"), OSError("Access is denied")],
    ids=["errno", "no errno"],
)
def test_what_the_os_refuses_is_listed_and_the_run_finishes(
    media, monkeypatch, owner, method, refused, error
):
    e = _legacy(media, "expense-type")

    def refuse(*args):
        raise error

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
