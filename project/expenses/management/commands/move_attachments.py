from django.core.management.base import BaseCommand

from ...services.attachment_folders import AttachmentFolders


class Command(BaseCommand):
    help = "Move stored attachments into their Expense type's pk folder."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would move and touch no file, folder or row.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        result = AttachmentFolders.move(dry_run=dry_run)

        for old, new in result.moved:
            self.stdout.write(f"{old} -> {new}")
        for old in result.missing:
            self.stdout.write(f"missing: {old}")
        for old in result.too_long:
            self.stdout.write(f"not moved: {old} (name too long)")
        for old, reason in result.not_deleted:
            self.stdout.write(f"not deleted: {old} ({reason})")
        for folder, reason in result.not_removed:
            self.stdout.write(f"not removed: {folder} ({reason})")

        prefix = "dry run: " if dry_run else ""
        self.stdout.write(
            f"{prefix}moved {len(result.moved)}, missing {len(result.missing)}"
        )
