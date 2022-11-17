from ..models import Book, BookTarget


class InfoRow():
    def __init__(self, year):
        self._year = year

    def context(self):
        return {
            'readed': self.readed(),
            'reading': self.reading(),
            'target': self.target(),
        }

    def readed(self):
        qs = \
            Book.objects \
            .readed() \
            .filter(year=self._year)

        return qs[0]['cnt'] if qs.exists() else 0

    def reading(self):
        return \
            qs['reading'] if (qs := Book.objects.reading(self._year)) else 0

    def target(self):
        try:
            qs = \
                BookTarget.objects \
                .related() \
                .get(year=self._year)
        except BookTarget.DoesNotExist:
            return 0

        return qs
