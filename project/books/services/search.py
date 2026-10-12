from ...core.lib.search import generic_search
from .model_services import BookModelService


def search_books(user, search_str):
    qs = generic_search(
        BookModelService(user).items(), search_str, ["author", "title"], "started"
    )

    return qs.values(
        "id",
        "author",
        "title",
        "remark",
        "started",
        "ended",
    )
