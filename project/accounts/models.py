from django.db import models
from django.db.models import (Case, Count, DecimalField, ExpressionWrapper, F,
                              Func, Max, Q, Sum, When)
from django.db.models.functions import TruncMonth

from ..core.models import TitleAbstract


class AccountQuerySet(models.QuerySet):
    def _sum_price(self, year, related_name, keyword_lookup):
        '''
        year: year

        related_name: ForeignKey related_name for account model

        keyword_lookup:
            lookup for current records related_name__date_year
            or
            past records related_name__date_year__lt
        '''
        return Sum(Case(
            When(
                **{keyword_lookup: year},
                then=f'{related_name}__price'),
            default=0
        ))

    def _sum_current_year(self, year, related_name):
        '''
        year: year

        related_name: ForeignKey related_name for account model
        '''
        lookup = f'{related_name}__date__year'

        return self._sum_price(year, related_name, lookup)

    def _sum_past_years(self, year, related_name):
        '''
        year: year

        related_name: ForeignKey related_name for account model
        '''
        lookup = f'{related_name}__date__year__lt'

        return self._sum_price(year, related_name, lookup)

    def _fix_multiplied_err(self, keyword_prefix, keyword_time):
        '''
        Functin for fixing chained .annotate multiplication error

        keyword_prefix: shortcut for related_name ie incomes == i

        keyword_time: values past (year < current) or now (year == current year)

        Returns:
        (multiplied_values * disctinct_count) / count
        '''
        return (
            ExpressionWrapper(
                (
                    F(f'{keyword_prefix}_multiplied_{keyword_time}')
                    * F(f'{keyword_prefix}_count_distinct')
                )
                / F(f'{keyword_prefix}_count'),
                output_field=DecimalField()
            )
        )

    def _annotate(self, year, related_name, keyword_prefix):
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
                multiplied_now: self._sum_current_year(year, related_name)
            })
            .annotate(** {
                multiplied_past: self._sum_past_years(year, related_name)
            })
            .annotate(**{
                now: self._fix_multiplied_err(keyword_prefix, 'now')
            })
            .annotate(**{
                now: Case(When(~Q(**{now: None}), then=now), default=0)
            })
            .annotate(**{
                past: self._fix_multiplied_err(keyword_prefix, 'past')
            })
            .annotate(**{
                past: Case(When(~Q(**{past: None}), then=past), default=0)
            })
        )

    def incomes(self, year):
        return self._annotate(year, 'incomes', 'i')

    def expenses(self, year):
        return self._annotate(year, 'expenses', 'e')

    def savings(self, year):
        return self._annotate(year, 'savings', 's')

    def transactions_from(self, year):
        return self._annotate(year, 'transactions_from', 'tr_from')

    def transactions_to(self, year):
        return self._annotate(year, 'transactions_to', 'tr_to')

    def savings_close_to(self, year):
        return self._annotate(year, 'savings_close_to', 's_close_to')

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
