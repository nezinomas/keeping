from dataclasses import dataclass

from ..models import Book, BookTarget


@dataclass
class InfoRow():
    year: int
    readed: int = 0
    reading: int = 0
    target: int = 0

    def __post_init__(self):
        self.readed = self._readed()
        self.reading = self._reading()
        self.target = self._target()

    def _readed(self):
        qs = \
            Book.objects \
            .readed() \
            .filter(year=self.year)

        return qs[0]['cnt'] if qs.exists() else 0.0

    def _reading(self):
        return \
            qs['reading'] if (qs := Book.objects.reading(self.year)) else 0

    def _target(self):
        try:
            qs = \
                BookTarget.objects \
                .related() \
                .get(year=self.year)
        except BookTarget.DoesNotExist:
            return 0

        return qs
