class MonthMixin:
    def get_month(self):
        month = self.request.GET.get("month")

        try:
            month = int(month)
        except (TypeError, ValueError):
            month = None

        month = month if month in range(1, 13) else None

        return month or self.request.user.month

    def set_month(self):
        get_month = self.get_month()
        user_month = self.request.user.month
        if get_month != user_month:
            user = self.request.user
            user.month = get_month
            user.save()
