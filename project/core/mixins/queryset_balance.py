from django.db.models import (Case, Count, DecimalField, ExpressionWrapper, F,
                              Sum, When)


class QuerySetBalanceMixin():
    def sum_price(self, year, related_name, keyword_lookup):
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

    def sum_current_year(self, year, related_name):
        '''
        year: year

        related_name: ForeignKey related_name for account model
        '''
        lookup = f'{related_name}__date__year'

        return self.sum_price(year, related_name, lookup)

    def sum_past_years(self, year, related_name):
        '''
        year: year

        related_name: ForeignKey related_name for account model
        '''
        lookup = f'{related_name}__date__year__lt'

        return self.sum_price(year, related_name, lookup)

    def fix_multiplied_err(self, keyword_prefix, keyword_time):
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
