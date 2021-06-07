from django.apps import AppConfig


class PensionsConfig(AppConfig):
    name = 'project.pensions'

    def ready(self):
        from ..core.signals import post_save_pension_stats
