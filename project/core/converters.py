class DateConverter:
    regex = r'(\d{8})'

    def to_python(self, value):
        return value

    def to_url(self, date):
        return date


class SignerConverter:
    regex = r'([\w\-]{23,}:[\w\-]{5,}:[\w\-]{43})'

    def to_python(self, value):
        return value

    def to_url(self, token):
        return token
