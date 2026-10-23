import re

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

PICKER_SCRIPT = r'<script[^>]*src="[^"]*/js/([a-z]+-picker\.js)"'


def clean_content(rendered):
    return str(rendered).replace("\n", "").replace("\t", "").replace("  ", "")


def quick_add_pills(content):
    """(tag, the tab it waits for or "", its url attribute, label) of each pill."""
    return re.findall(
        r"<(a|button)(?:[^>]*x-show=\"tab === '(\w+)'\" x-cloak)?[^>]*"
        r' class="quick-add__pill" ((?:href|hx-get)="[^"]*")[^>]*>([^<]*)</\1>',
        content,
    )


def count_queries(run):
    with CaptureQueriesContext(connection) as queries:
        run()
    return len(queries)


def change_profile_year(client, year=1):
    url = reverse("bookkeeping:index")
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


def view_for(rf, user, view_class, path="/", **kwargs):
    request = rf.get(path)
    request.user = user
    return setup_view(view_class(), request, **kwargs)
