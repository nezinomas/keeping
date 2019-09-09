from django.db import models
from django.db.models import Count, F, Func
from django.db.models.functions import TruncMonth

from ..core.mixins.queryset_balance import QuerySetBalanceMixin
from ..core.models import TitleAbstract


class AccountQuerySet(QuerySetBalanceMixin, models.QuerySet):
    def incomes(self, year):
        return self.annotate_(year, 'incomes', 'i')

    def expenses(self, year):
        return self.annotate_(year, 'expenses', 'e')

    def savings(self, year):
        return self.annotate_(year, 'savings', 's')

    def transactions_from(self, year):
        return self.annotate_(year, 'transactions_from', 'tr_from')

    def transactions_to(self, year):
        return self.annotate_(year, 'transactions_to', 'tr_to')

    def savings_close_to(self, year):
        return self.annotate_(year, 'savings_close_to', 's_close_to')

    # def accounts_worth(self):
    #     return (
    #         self
    #         .latest()
    #         .annotate(max_date=Max('accounts_worth__date'))
    #         .filter(accounts_worth__date=F('max_date'))
    #         .annotate(have=F('accounts_worth__price'))
    #     )

    def balance_year(self, year):
        return (
            self
            .annotate(a=Count('title', distinct=True)).values(account=F('title'))
            .incomes(year)
            .expenses(year)
            .savings(year)
            .transactions_from(year)
            .transactions_to(year)
            .savings_close_to(year)
            .annotate(
                past=(
                    0
                    + F('i_past')
                    - F('e_past')
                    - F('s_past')
                    - F('tr_from_past')
                    + F('tr_to_past')
                    + F('s_close_to_past')
                )
            )
            .annotate(
                incomes=(
                    0
                    + F('i_now')
                    + F('tr_to_now')
                    + F('s_close_to_now')
                )
            )
            .annotate(
                expenses=Func((
                    0
                    - F('e_now')
                    - F('s_now')
                    - F('tr_from_now')
                ), function='abs')
            )
            .annotate(
                balance=(
                    0
                    + F('past')
                    + F('incomes')
                    - F('expenses')
                )
            )
            .values('account', 'past', 'incomes', 'expenses', 'balance')
            .order_by('title')
        )


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=10
    )

    class Meta:
        ordering = ['order', 'title']

    # Managers
    objects = AccountQuerySet.as_manager()
