from django.apps import AppConfig

App_name = 'bookkeeping'


class bookkeepingConfig(AppConfig):
    name = f'project.{App_name}'

    def ready(self):
        from ..core.signals import savings_post_signal
