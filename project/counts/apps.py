from django.apps import AppConfig

App_name = "counts"


class Config(AppConfig):
    name = f"project.{App_name}"

    def ready(self) -> None:
        from .signals import generate_counts_menu
