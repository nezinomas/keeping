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
    # Fields to subtract when sold is truthy
    subtract_fields = {"incomes", "profit_sum"}

    # Initialize result dictionary
    row = {field: 0 for field in fields}

    # Process each object
    for obj in data:
        # Get all field values in one pass
        values = obj.__dict__
        sold = values.get("sold", 0)

        # Update sums for all fields
        for field in fields:
            if field in subtract_fields and sold:
                continue

            value = values.get(field, 0)
            row[field] += value

    # Update profit_proc if applicable
    if "profit_proc" in fields and row.get("market_value"):
        row["profit_proc"] = calculate_percents(row)

    return row


def calculate_percents(data):
    incomes = data.get("incomes", 0)
    fee = data.get("fee", 0)
    market_value = data.get("market_value", 0)

    return ((market_value - fee) / incomes * 100) - 100 if incomes else 0


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
        headers = {
            "HX-Trigger": json.dumps({hx_trigger_name: None}),
        }

    return HttpResponse(
        status=status_code,
        headers=headers,
    )