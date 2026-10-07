from django.apps import AppConfig

App_name = "bookkeeping"


class BookkeepingConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from . import signals  # noqa: F401
