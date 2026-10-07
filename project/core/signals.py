from django.db import models
from django.db.models.signals import post_delete, post_save

from ..bookkeeping import balance_sources
from .services.signals_service import journal_user


def connect_save_and_delete(receiver, *senders):
    for sender in senders:
        post_save.connect(receiver, sender=sender)
        post_delete.connect(receiver, sender=sender)


def accounts_signal(sender: object, instance: models.Model, *args, **kwargs):
    balance_sources.sync_accounts(journal_user(instance))


def savings_signal(sender: object, instance: models.Model, *args, **kwargs):
    balance_sources.sync_savings(journal_user(instance))


def pensions_signal(sender: object, instance: models.Model, *args, **kwargs):
    balance_sources.sync_pensions(journal_user(instance))


def update_journal_first_record(sender, instance, created, **kwargs):
    journal = instance.journal

    if journal.first_record > instance.date:
        journal.first_record = instance.date
        journal.save(update_fields=["first_record"])
