import contextlib
import json
from functools import lru_cache
from urllib.parse import urlparse

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import Resolver404, resolve, reverse
from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_redirect(request, url, fallback="/"):
    if not url or not url_has_allowed_host_and_scheme(
        url=url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return fallback

    with contextlib.suppress(Resolver404):
        path = urlparse(url).path
        if resolve(path):
            return path

    return fallback


def total_row(data, fields: list[str]) -> dict:
    row = {field: 0 for field in fields}

    for obj in data:
        values = obj.__dict__
        for field in fields:
            row[field] += values.get(field, 0)

    return row


def funds_total_row(data, fields: list[str], switched_within: int = 0) -> dict:
    """The funds tables' Total row: profit and % read only the rows showing one."""
    row = total_row(data, [f for f in fields if f != "profit_proc"])
    shown = [obj for obj in data if obj.shows_profit]
    shown_row = total_row(shown, ["incomes", "profit_sum"])
    row["profit_sum"] = shown_row["profit_sum"]
    row["profit_proc"] = profit_percent(shown_row, switched_within)
    return row


def profit_percent(row: dict, switched_within: int = 0) -> float:
    base = row.get("incomes", 0) - switched_within
    if base <= 0:
        return 0.0

    return row.get("profit_sum", 0) / base * 100


@lru_cache(maxsize=1)
def get_action_buttons_html() -> dict[str, str]:
    """
    Returns the pre-compiled HTML strings for the action buttons.
    Cached indefinitely since the template code doesn't change during runtime.
    """
    return {
        "edit_col": render_to_string("cotton/td_edit.html", {"url": "[[url]]"}),
        "delete_col": render_to_string("cotton/td_delete.html", {"url": "[[url]]"}),
    }


def add_fast_urls(
    data: list[dict], update: str, delete: str, pk_key: str = "id"
) -> list[dict]:
    """Each row's update and delete url, reversed once per list rather than per row."""
    if not data:
        return []

    update_head, update_tail = _around_pk(update)
    delete_head, delete_tail = _around_pk(delete)

    return [
        {
            **row,
            "url_update": f"{update_head}{row[pk_key]}{update_tail}",
            "url_delete": f"{delete_head}{row[pk_key]}{delete_tail}",
        }
        for row in data
    ]


def _around_pk(url_name: str) -> tuple[str, str]:
    head, _, tail = reverse(url_name, args=[0]).rpartition("0")
    return head, tail


def rendered_content(request, view_class, **kwargs):
    request.resolver_match.kwargs.update(kwargs)

    return view_class.as_view()(request, **kwargs).rendered_content


def wants_fragment(request) -> bool:
    htmx = request.htmx
    return bool(htmx) and not htmx.history_restore_request


def http_htmx_response(hx_trigger_name=""):
    headers = {}
    if hx_trigger_name:
        # {} and not None: htmx 4 reads the detail off the header and throws on a
        # null one, which aborts the response before the event is ever dispatched
        headers = {
            "HX-Trigger": json.dumps({hx_trigger_name: {}}),
        }

    return HttpResponse(
        status=204,
        headers=headers,
    )


def int_or_zero(value) -> int:
    number = 0
    with contextlib.suppress(TypeError, ValueError):
        number = int(value)
    return number
