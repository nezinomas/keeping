from django.apps import AppConfig

App_name = 'bookkeeping'


class bookkeepingConfig(AppConfig):
    name = f'project.{App_name}'

    def ready(self):
        from ..core.signals import (post_save_account_stats,
                                    post_save_saving_stats)
