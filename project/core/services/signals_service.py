from django.db import models

from ...users.models import User
from ..lib.db_sync import BalanceSynchronizer
from ..lib.signals import GetData


def sync(user: User, conf: dict, table: type, balance_service: type) -> None:
    data = table(GetData(user, conf))
    BalanceSynchronizer(balance_service, user, data.df)


def journal_user(instance: models.Model) -> User:
    return instance.journal.users.earliest("pk")
