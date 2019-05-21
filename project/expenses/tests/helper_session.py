from django.contrib.sessions.middleware import SessionMiddleware


def add_session_to_request(request, *args, **kwargs):
    """Annotate a request object with a session"""
    middleware = SessionMiddleware()
    middleware.process_request(request)

    if 'year' in kwargs:
        request.session['year'] = kwargs['year']

    request.session.save()
