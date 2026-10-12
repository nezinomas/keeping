import posixpath
from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage
from django.db import transaction

from ..helpers.models_helper import attachment_folder
from ..models import Expense


@dataclass
class AttachmentMoves:
    moved: list[tuple[str, str]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    too_long: list[str] = field(default_factory=list)
    not_deleted: list[tuple[str, str]] = field(default_factory=list)
    not_removed: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class AttachmentFolders:
    dry_run: bool = False

    @classmethod
    def move(cls, dry_run: bool = False) -> AttachmentMoves:
        return cls(dry_run)._move()

    def _move(self) -> AttachmentMoves:
        result = AttachmentMoves()
        changed = []
        copies = {}
        too_long = set()
        pending, in_place = self._read()

        for old, rows in pending.items():
            if not default_storage.exists(old):
                result.missing.extend(old for _ in rows)
                continue

            for expense, folder in rows:
                key = (old, posixpath.join(folder, posixpath.basename(old)))
                if key not in copies.keys() | too_long:
                    try:
                        copies[key] = self._place(*key)
                    except SuspiciousFileOperation:
                        too_long.add(key)
                if key in too_long:
                    result.too_long.append(old)
                    continue

                expense.attachment = copies[key]
                changed.append(expense)
                result.moved.append((old, copies[key]))

        if self.dry_run:
            return result

        with transaction.atomic():
            Expense.objects.bulk_update(changed, ["attachment"])
        olds = {old for old, _ in copies} - in_place - {old for old, _ in too_long}
        result.not_deleted.extend(self._delete(olds))
        result.not_removed.extend(
            self._remove_emptied({posixpath.dirname(old) for old in olds})
        )
        return result

    @staticmethod
    def _read() -> tuple[dict[str, list[tuple[Expense, str]]], set[str]]:
        pending = {}
        in_place = set()
        rows = Expense.objects.exclude(attachment="").select_related("expense_type")
        for expense in rows:
            old = expense.attachment.name
            folder = attachment_folder(expense.expense_type).as_posix()
            if posixpath.dirname(old) == folder:
                in_place.add(old)
                continue
            pending.setdefault(old, []).append((expense, folder))
        return pending, in_place

    def _place(self, old: str, new: str) -> str:
        max_length = Expense._meta.get_field("attachment").max_length
        if self.dry_run:
            return default_storage.get_available_name(new, max_length=max_length)
        with default_storage.open(old) as file:
            return default_storage.save(new, file, max_length=max_length)

    @staticmethod
    def _delete(olds: set[str]) -> list[tuple[str, str]]:
        refused = []
        for old in sorted(olds):
            try:
                default_storage.delete(old)
            except OSError as error:
                refused.append((old, error.strerror))
        return refused

    @staticmethod
    def _remove_emptied(folders: set[str]) -> list[tuple[str, str]]:
        refused = []
        for folder in sorted(folders):
            dirs, files = default_storage.listdir(folder)
            if dirs or files:
                continue
            try:
                Path(default_storage.path(folder)).rmdir()
            except OSError as error:
                refused.append((folder, error.strerror))
        return refused
