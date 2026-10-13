import itertools
import posixpath
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from ..helpers.models_helper import attachment_folder
from ..models import Expense


@dataclass
class AttachmentMoves:
    moved: list[tuple[str, str]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    too_long: list[str] = field(default_factory=list)
    not_copied: list[tuple[str, str]] = field(default_factory=list)
    not_deleted: list[tuple[str, str]] = field(default_factory=list)
    not_removed: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class AttachmentFolders:
    dry_run: bool = False
    taken: set[str] = field(default_factory=set, init=False)

    @classmethod
    def move(cls, dry_run: bool = False) -> AttachmentMoves:
        return cls(dry_run)._move()

    def _move(self) -> AttachmentMoves:
        result = AttachmentMoves()
        changed = []
        copies = {}
        too_long = set()
        not_copied = {}
        pending, in_place = self._read()
        # a file a row names, now or before the move, is never handed to another row
        self.taken |= in_place | pending.keys()

        for old, rows in pending.items():
            if not default_storage.exists(old):
                result.missing.extend(old for _ in rows)
                continue

            for expense, folder in rows:
                key = (old, posixpath.join(folder, posixpath.basename(old)))
                if key not in copies.keys() | too_long | not_copied.keys():
                    try:
                        copies[key] = self._place(*key)
                    except SuspiciousFileOperation:
                        too_long.add(key)
                    except OSError as error:
                        not_copied[key] = _reason(error)
                if key in too_long:
                    result.too_long.append(old)
                    continue
                if key in not_copied:
                    result.not_copied.append((old, not_copied[key]))
                    continue

                expense.attachment = copies[key]
                changed.append(expense)
                result.moved.append((old, copies[key]))

        if self.dry_run:
            return result

        with transaction.atomic():
            Expense.objects.bulk_update(changed, ["attachment"])
        still_named = {old for old, _ in too_long | not_copied.keys()}
        olds = {old for old, _ in copies} - in_place - still_named
        result.not_deleted.extend(self._delete(olds))
        result.not_removed.extend(
            self._remove_emptied({posixpath.dirname(old) for old in olds})
        )
        return result

    @staticmethod
    def _read() -> tuple[dict[str, list[tuple[Expense, str]]], set[str]]:
        pending = {}
        in_place = set()
        rows = (
            Expense.objects.exclude(attachment="")
            .select_related("expense_type")
            .order_by("pk")
        )
        for expense in rows:
            old = expense.attachment.name
            folder = attachment_folder(expense.expense_type).as_posix()
            if posixpath.dirname(old) == folder:
                in_place.add(old)
                continue
            pending.setdefault(old, []).append((expense, folder))
        return pending, in_place

    def _place(self, old: str, new: str) -> str:
        content = self._read_bytes(old)
        name = next(name for name in self._names(new) if self._free(name, content))
        self.taken.add(name)
        if self.dry_run or default_storage.exists(name):
            return name
        try:
            return default_storage.save(name, ContentFile(content))
        except OSError:
            # the storage leaves a half-written file behind
            if default_storage.exists(name):
                default_storage.delete(name)
            raise

    def _free(self, name: str, content: bytes) -> bool:
        if name in self.taken:
            return False
        # an equal file is the copy an earlier, crashed run left behind
        return not default_storage.exists(name) or self._read_bytes(name) == content

    @staticmethod
    def _names(new: str) -> Iterator[str]:
        max_length = Expense._meta.get_field("attachment").max_length
        root, ext = posixpath.splitext(new)
        numbered = (f"{root}_{n}{ext}" for n in itertools.count(2))
        for name in itertools.chain([new], numbered):
            if len(name) > max_length:
                raise SuspiciousFileOperation(f"{name} is longer than {max_length}")
            yield name

    @staticmethod
    def _read_bytes(name: str) -> bytes:
        with default_storage.open(name) as file:
            return file.read()

    @staticmethod
    def _delete(olds: set[str]) -> list[tuple[str, str]]:
        refused = []
        for old in sorted(olds):
            try:
                default_storage.delete(old)
            except OSError as error:
                refused.append((old, _reason(error)))
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
                refused.append((folder, _reason(error)))
        return refused


def _reason(error: OSError) -> str:
    # strerror is None for an OSError raised without an errno
    return error.strerror or str(error)
