from django.apps import AppConfig


class SavingsConfig(AppConfig):
    name = 'project.savings'

    def ready(self):
        from ..core.signals import (accounts_post_delete, accounts_post_save,
                                    savings_post_delete, savings_post_save)
