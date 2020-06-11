class DateConverter:
    regex = r'(\d{8})'

    def to_python(self, value):
        return value

    def to_url(self, date):
        return date
