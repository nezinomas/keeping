from django.utils import translation


class JournalLanguageMiddleware:
    """A logged-in user reads their journal's language, not the cookie's."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        lang = request.user.journal.lang
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        return self.get_response(request)
