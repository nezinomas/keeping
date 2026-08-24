import threading

_lock = threading.Lock()


def serialize_requests(get_response):
    # Every live server thread shares one in-memory sqlite connection, so two
    # requests at once wedge it -- the expenses page loads two panels at once.
    def middleware(request):
        with _lock:
            return get_response(request)

    return middleware
