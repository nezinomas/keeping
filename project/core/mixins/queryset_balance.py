from django.db.models import (Case, Count, DecimalField, ExpressionWrapper, F,
                              Func, Max, Q, Sum, When)


class QuerySetBalanceMixin():
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
