from datetime import date, datetime
from zoneinfo import ZoneInfo

from ....accounts.tests.factories import AccountFactory
from ....bookkeeping.tests.factories import SavingWorthFactory
from ....savings.models import SavingBalance
from ....savings.tests.factories import (
    SavingFactory,
    SavingTypeFactory,
)
from ....transactions.tests.factories import SavingChangeFactory, SavingCloseFactory

TZ = ZoneInfo("Europe/Vilnius")
YEAR = 1999


def worth_date(month=12, day=31, year=YEAR):
    return datetime(year, month, day, 12, tzinfo=TZ)


def balance(saving_type, year=YEAR):
    return SavingBalance.objects.get(saving_type=saving_type, year=year)


def buy(saving_type, price, fee=0, when=date(YEAR, 1, 1)):
    return SavingFactory(saving_type=saving_type, price=price, fee=fee, date=when)


def sell(saving_type, price, fee=0, when=date(YEAR, 6, 1)):
    return SavingCloseFactory(
        from_account=saving_type,
        to_account=AccountFactory(title="Bank"),
        price=price,
        fee=fee,
        date=when,
    )


def worth(saving_type, price, month=12, day=31, year=YEAR):
    return SavingWorthFactory(
        saving_type=saving_type, price=price, date=worth_date(month, day, year)
    )


def switch_out(fund, price, when):
    return SavingChangeFactory(
        from_account=fund,
        to_account=SavingTypeFactory(title="Other"),
        price=price,
        fee=0,
        date=when,
    )
