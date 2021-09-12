from django.apps import AppConfig


class SavingsConfig(AppConfig):
    name = 'project.savings'

    def ready(self):
        from ..core.signals import (accounts_post_signal,
                                    savings_post_signal)
