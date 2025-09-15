import os
from datetime import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from time_machine import travel


class Command(BaseCommand):
    help = (
        "Runs the Django development server with a custom date, "
        "overriding datetime.now() using time_machine."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default=None,
            help="Set a custom date (YYYY-MM-DD) for the application.",
        )
        parser.add_argument(
            "--port",
            default="8000",
            help="Port number for the server (default: 8000).",
        )
        parser.add_argument(
            "--noreload",
            action="store_true",
            help="Disable the auto-reloader.",
        )

    def handle(self, *args, **options):
        freezer = None
        if custom_date := options.get("date"):
            try:
                parsed_date = datetime.strptime(custom_date, "%Y-%m-%d")
                os.environ["DJANGO_CUSTOM_DATE"] = custom_date
                freezer = travel(parsed_date, tick=False)
                freezer.start()
            except ValueError as e:
                raise CommandError("Invalid date format. Use YYYY-MM-DD.") from e

        port = options.get("port")
        addrport = f"127.0.0.1:{port}"
        runserver_options = {
            "addrport": addrport,
            "use_reloader": not options.get("noreload"),
        }
        try:
            call_command("runserver", **runserver_options)
        except Exception as e:
            raise
        finally:
            if freezer:
                freezer.stop()
