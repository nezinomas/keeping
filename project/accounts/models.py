from django.db import models
from django.db.models import Case, Count, F, Func, Q, When
from django.db.models.functions import TruncMonth

from ..core.mixins.queryset_balance import QuerySetBalanceMixin
from ..core.models import TitleAbstract


class AccountQuerySet(QuerySetBalanceMixin, models.QuerySet):
    def annotate_(self, year, related_name, keyword_prefix):
        '''
        year: year

        related_name: ForeignKey related_name for account model

        keyword_prefix: shortcut for related_name - incomes == i
        '''
        count = f'{keyword_prefix}_count'
        count_distinct = f'{keyword_prefix}_count_distinct'
        multiplied_now = f'{keyword_prefix}_multiplied_now'
        multiplied_past = f'{keyword_prefix}_multiplied_past'
        now = f'{keyword_prefix}_now'
        past = f'{keyword_prefix}_past'

        return (
            self
            .annotate(**{
                count: Count(related_name)
            })
            .annotate(**{
                count_distinct: Count(related_name, distinct=True)
            })
            .annotate(**{
                multiplied_now: self.sum_current_year(year, related_name)
            })
            .annotate(** {
                multiplied_past: self.sum_past_years(year, related_name)
            })
            .annotate(**{
                now: self.fix_multiplied_err(keyword_prefix, 'now')
            })
            .annotate(**{
                now: Case(When(~Q(**{now: None}), then=now), default=0)
            })
            .annotate(**{
                past: self.fix_multiplied_err(keyword_prefix, 'past')
            })
            .annotate(**{
                past: Case(When(~Q(**{past: None}), then=past), default=0)
            })
        )

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
    #         .annotate(max_date=counts_worth__date'))
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
