from django.apps import AppConfig


class SavingsConfig(AppConfig):
    name = 'project.savings'

    def ready(self):
        from ..core.signals import savings_post_signal
