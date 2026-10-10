from datetime import date

import pytest

from ...services.search import search_books
from ..factories import BookFactory

BOOK = ("Author", "Book Title", "Remark")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "_search, books",
    [
        ("1999", [BOOK]),
        ("-y1999", [BOOK]),
        ("1999.1", [BOOK]),
        ("1999-1", [BOOK]),
        ("-y 1999 -m 1", [BOOK]),
        ("2000", []),
        ("-y 2000", []),
        ("a", []),
        ("ab", []),
        ("auth", [BOOK]),
        ("-c auth", [BOOK]),
        ("titl", [BOOK]),
        ("-c titl", [BOOK]),
        ("remark", [BOOK]),
        ("-r remark", [BOOK]),
        ("1999.1 auth", [BOOK]),
        ("1999-1 auth", [BOOK]),
        ("-r 1999 -m 1 -c auth", []),
        ("-y 1999 -m 1 -c auth", [BOOK]),
        ("1999.1 titl", [BOOK]),
        ("1999-1 titl", [BOOK]),
        ("-y 1999 -m 1 -c titl", [BOOK]),
    ],
)
def test_books_search(main_user, _search, books):
    BookFactory()
    BookFactory(started=date(3333, 1, 1), author="A", title="T", remark="ZZZ")

    actual = [
        (row["started"], row["author"], row["title"], row["remark"])
        for row in search_books(main_user, _search)
    ]

    assert actual == [(date(1999, 1, 1), *book) for book in books]
