import functools
import time

from django.urls import reverse


def _remove_line_end(rendered):
    return str(rendered).replace('\n', '').replace('\t', '')


def change_profile_year(client, year=1):
    url = reverse('bookkeeping:index')
    response = client.get(url)

    u = response.wsgi_request.user
    u.year = year
    u.save()


def setup_view(view, request, *args, **kwargs):
    """
    Mimic ``as_view()``, but returns view instance.
    Use this function to get view instances on which you can run unit tests,
    by testing specific methods.
    """

    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


def timer(func):
    @functools.wraps(func)
    def wrap_func(*args, **kwargs):
        start = time.perf_counter()
        return_value = func(*args, **kwargs)
        end = time.perf_counter()
        total = end-start
        print(f'Finished function: {func.__name__} in {total:.4f} sec')
        return return_value
    return wrap_func


class Timer:
    def __init__(self, original_func):
        self.original_func = original_func

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        r_val = self.original_func(*args, **kwargs)
        end = time.perf_counter()
        total = end - start
        print(f'Finished function form class: {self.original_func.__name__} in {total:.5f} sec')
        return r_val
