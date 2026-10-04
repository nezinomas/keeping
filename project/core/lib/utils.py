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


def total_row(data, fields: list[str], switched_within: int = 0) -> dict:
    row = {field: 0 for field in fields}

    for obj in data:
        values = obj.__dict__
        for field in fields:
            row[field] += values.get(field, 0)

    if "profit_proc" in fields:
        row["profit_proc"] = profit_percent(row, switched_within)

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


def add_fast_urls(data: list[dict], app_name: str, pk_key: str = "id") -> list[dict]:
    """
    Fast URL generation for lists of dictionaries.
    Replaces database-level Concat to decouple DB from Routing.
    """

    if not data:
        return []

    dummy_id = "0"

    # 1. Ask Django's router for the template EXACTLY ONCE
    url_update = reverse(f"{app_name}:update", args=[dummy_id])
    url_delete = reverse(f"{app_name}:delete", args=[dummy_id])

    # 2. Fast Python string replacement in memory
    return [
        {
            **row,
            "url_update": url_update.replace(dummy_id, str(row.get(pk_key))),
            "url_delete": url_delete.replace(dummy_id, str(row.get(pk_key))),
        }
        for row in data
    ]


def rendered_content(request, view_class, **kwargs):
    # update request kwargs
    request.resolver_match.kwargs.update({**kwargs})

    return view_class.as_view()(request, **kwargs).rendered_content


def http_htmx_response(hx_trigger_name=None, status_code=204):
    headers = {}
    if hx_trigger_name:
        # {} and not None: htmx 4 reads the detail off the header and throws on a
        # null one, which aborts the response before the event is ever dispatched
        headers = {
            "HX-Trigger": json.dumps({hx_trigger_name: {}}),
        }

    return HttpResponse(
        status=status_code,
        headers=headers,
    )


def int_or_zero(value) -> int:
    number = 0
    with contextlib.suppress(TypeError, ValueError):
        number = int(value)
    return number
