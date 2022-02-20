from django.apps import AppConfig

App_name = 'bookkeeping'


class bookkeepingConfig(AppConfig):
    name = f'project.{App_name}'

    def ready(self):
        from ..core.signals import (accounts_post_save, pensions_post_save,
                                    savings_post_save)

