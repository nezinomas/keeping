from django.db.models import Model

from ..core.services import signals_service
from .services.close_year import FundCloseYear


def move_signal(sender: object, instance: Model, *args, **kwargs):
    # the close year first: the savings sync reads it
    FundCloseYear.follow(instance.from_account_id, instance.close_rule)
    for fund_pk in instance.left_funds:
        FundCloseYear.follow(fund_pk)
    instance.settle()

    signals_service.sync_savings(signals_service.journal_user(instance))
