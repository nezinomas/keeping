from datetime import datetime


class DateConverter:
    regex = r"(\d{4}-\d{1,2}-\d{1,2})"

    def to_python(self, value):
        return datetime.strptime(value, "%Y-%m-%d").date()

    def to_url(self, value):
        try:
            return value.strftime("%Y-%m-%d")
        except AttributeError:
            return "1974-1-1"


class SignerConverter:
    regex = r"([\w\-]{23,}:[\w\-]{5,}:[\w\-]{43})"

    def to_python(self, value):
        return value

    def to_url(self, token):
        return token
