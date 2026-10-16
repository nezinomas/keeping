import itertools
import posixpath
from collections.abc import Iterator
from dataclasses import dataclass, field

from django.core.files.storage import default_storage
from django.db import transaction

from ..helpers.models_helper import attachment_folder
from ..models import Expense


@dataclass(frozen=True)
class Copied:
    name: str


@dataclass(frozen=True)
class TooLong:
    pass


@dataclass(frozen=True)
class NotCopied:
    reason: str


Placement = Copied | TooLong | NotCopied


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
        placements = {}
        pending, in_place = self._read()
        # a file a row names, now or before the move, is never handed to another row
        self.taken |= in_place | pending.keys()

        for old, rows in pending.items():
            if not default_storage.exists(old):
                result.missing.extend(old for _ in rows)
                continue

            for expense, folder in rows:
                key = (old, posixpath.join(folder, posixpath.basename(old)))
                if key not in placements:
                    placements[key] = self._place(*key)

                match placements[key]:
                    case TooLong():
                        result.too_long.append(old)
                    case NotCopied(reason):
                        result.not_copied.append((old, reason))
                    case Copied(name):
                        expense.attachment = name
                        changed.append(expense)
                        result.moved.append((old, name))

        if self.dry_run:
            return result

        with transaction.atomic():
            Expense.objects.bulk_update(changed, ["attachment"])
        still_named = {
            old
            for (old, _), placed in placements.items()
            if not isinstance(placed, Copied)
        }
        olds = {old for old, _ in placements} - in_place - still_named
        result.not_deleted.extend(_delete(olds))
        emptied = {posixpath.dirname(old) for old in olds}
        result.not_removed.extend(_delete({f for f in emptied if _is_empty(f)}))
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

    def _place(self, old: str, new: str) -> Placement:
        try:
            return self._copy(old, new)
        except OSError as error:
            return NotCopied(_reason(error))

    def _copy(self, old: str, new: str) -> Placement:
        # opened in a dry run too, so both runs refuse a file the OS will not hand over
        default_storage.open(old).close()
        for name in _names(new):
            if self._free(name, old):
                break
        else:
            return TooLong()

        self.taken.add(name)
        if self.dry_run or default_storage.exists(name):
            return Copied(name)
        try:
            with default_storage.open(old) as file:
                return Copied(default_storage.save(name, file))
        except OSError:
            # the storage leaves a half-written file behind
            if default_storage.exists(name):
                default_storage.delete(name)
            raise

    def _free(self, name: str, old: str) -> bool:
        if name in self.taken:
            return False
        # an equal file is the copy an earlier, crashed run left behind
        return not default_storage.exists(name) or _same(name, old)


def _names(new: str) -> Iterator[str]:
    max_length = Expense._meta.get_field("attachment").max_length
    root, ext = posixpath.splitext(new)
    numbered = (f"{root}_{n}{ext}" for n in itertools.count(2))
    names = itertools.chain([new], numbered)
    return itertools.takewhile(lambda name: len(name) <= max_length, names)


def _same(one: str, other: str) -> bool:
    if default_storage.size(one) != default_storage.size(other):
        return False
    with default_storage.open(one) as a, default_storage.open(other) as b:
        return all(x == y for x, y in zip(a.chunks(), b.chunks()))


def _is_empty(folder: str) -> bool:
    dirs, files = default_storage.listdir(folder)
    return not dirs and not files


def _delete(names: set[str]) -> list[tuple[str, str]]:
    # the file system storage removes an empty folder as it removes a file
    refused = []
    for name in sorted(names):
        try:
            default_storage.delete(name)
        except OSError as error:
            refused.append((name, _reason(error)))
    return refused


def _reason(error: OSError) -> str:
    # strerror is None for an OSError raised without an errno
    return error.strerror or str(error)
