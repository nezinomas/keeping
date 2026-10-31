from django.db import models

from ...users.models import User
from ..lib.balance_rows import BalanceSources
from ..lib.db_sync import BalanceSynchronizer


def sync(user: User, conf: dict, table: type, balance_service: type) -> None:
    rows = table(BalanceSources(user, conf)).rows
    BalanceSynchronizer(balance_service, user, rows)


def journal_user(instance: models.Model) -> User:
    return instance.journal.users.earliest("pk")
