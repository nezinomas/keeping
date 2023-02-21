from django.db.models import F

from ..bookkeeping.models import AccountWorth, PensionWorth, SavingWorth
from ..debts.models import Debt, DebtReturn
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import Pension
from ..plans.models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                             SavingPlan)
from ..savings.models import Saving
from ..transactions.models import SavingChange, SavingClose, Transaction


def run():
    Income.objects.all().update(price=F('price')*100)
    Expense.objects.all().update(price=F('price')*100)
    Saving.objects.all().update(price=F('price')*100, fee=F('fee')*100)
    Transaction.objects.all().update(price=F('price')*100)
    SavingClose.objects.all().update(price=F('price')*100, fee=F('fee')*100)
    SavingChange.objects.all().update(price=F('price')*100, fee=F('fee')*100)
    Debt.objects.all().update(price=F('price')*100, returned=F('returned')*100)
    DebtReturn.objects.all().update(price=F('price')*100)
    AccountWorth.objects.all().update(price=F('price')*100)
    PensionWorth.objects.all().update(price=F('price')*100)
    SavingWorth.objects.all().update(price=F('price')*100)
    Pension.objects.all().update(price=F('price')*100, fee=F('fee')*100)

    # plans
    IncomePlan.objects.all().update(
        january=F('january')*100,
        february=F('february')*100,
        march=F('march')*100,
        april=F('april')*100,
        may=F('may')*100,
        june=F('june')*100,
        july=F('july')*100,
        august=F('august')*100,
        september=F('september')*100,
        october=F('october')*100,
        november=F('november')*100,
        december=F('december')*100,
    )

    ExpensePlan.objects.all().update(
        january=F('january')*100,
        february=F('february')*100,
        march=F('march')*100,
        april=F('april')*100,
        may=F('may')*100,
        june=F('june')*100,
        july=F('july')*100,
        august=F('august')*100,
        september=F('september')*100,
        october=F('october')*100,
        november=F('november')*100,
        december=F('december')*100,
    )

    SavingPlan.objects.all().update(
        january=F('january')*100,
        february=F('february')*100,
        march=F('march')*100,
        april=F('april')*100,
        may=F('may')*100,
        june=F('june')*100,
        july=F('july')*100,
        august=F('august')*100,
        september=F('september')*100,
        october=F('october')*100,
        november=F('november')*100,
        december=F('december')*100,
    )

    DayPlan.objects.all().update(
        january=F('january')*100,
        february=F('february')*100,
        march=F('march')*100,
        april=F('april')*100,
        may=F('may')*100,
        june=F('june')*100,
        july=F('july')*100,
        august=F('august')*100,
        september=F('september')*100,
        october=F('october')*100,
        november=F('november')*100,
        december=F('december')*100,
    )

    NecessaryPlan.objects.all().update(
        january=F('january')*100,
        february=F('february')*100,
        march=F('march')*100,
        april=F('april')*100,
        may=F('may')*100,
        june=F('june')*100,
        july=F('july')*100,
        august=F('august')*100,
        september=F('september')*100,
        october=F('october')*100,
        november=F('november')*100,
        december=F('december')*100,
    )
