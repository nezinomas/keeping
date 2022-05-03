from django.db.models import Count, Sum
from django.db.models import F
from django.db.models.functions import (ExtractYear, TruncDay, TruncMonth,
                                        TruncYear)


class SumMixin():
    def year_filter(self, year, field='date'):
        if year:
            return self.filter(**{f'{field}__year': year})

        return self
    year_filter.queryset_only = True

    def month_filter(self, month, field='date'):
        if month:
            return self.filter(**{f'{field}__month': month})

        return self
    month_filter.queryset_only = True

    def year_sum(self,
                 year=None,
                 sum_annotation='sum',
                 groupby='id',
                 sum_column='price'):
        return (
            self
            .year_filter(year)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncYear('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
            .annotate(year=ExtractYear(F('date')))
            .values('year', sum_annotation)
        )

    def month_sum(self,
                  year,
                  month=None,
                  sum_annotation='sum',
                  sum_column='price',
                  groupby='id'):
        return (
            self
            .year_filter(year)
            .month_filter(month)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
            .values('date', sum_annotation)
        )

    def day_sum(self,
                year,
                month=None,
                sum_annotation='sum',
                sum_column='price',
                groupby='id'):
        return (
            self
            .year_filter(year)
            .month_filter(month)
            .annotate(c=Count(groupby))
            .values('c')
            .annotate(date=TruncDay('date'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
            .values('date', sum_annotation)
        )
