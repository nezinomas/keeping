import pytest
from django.utils.safestring import SafeString

from ...templatetags.fast_rendering import inject_url


@pytest.mark.parametrize(
    "template, url, expect",
    [
        pytest.param(
            '<a href="[[url]]">Edit</a>',
            "/expenses/update/123/",
            '<a href="/expenses/update/123/">Edit</a>',
            id="success",
        ),
        pytest.param(
            '<a href="[[url]]" data-hx-get="[[url]]">Link</a>',
            "/foo/bar/",
            '<a href="/foo/bar/" data-hx-get="/foo/bar/">Link</a>',
            id="multiple_occurrences",
        ),
        pytest.param(
            "<span>No link here</span>",
            "/somewhere/",
            "<span>No link here</span>",
            id="no_placeholder",
        ),
        pytest.param("", "/url/", "", id="empty_template"),
        pytest.param(None, "/url/", "", id="none_template"),
        pytest.param("ID: [[url]]", 123, "ID: 123", id="non_string_url"),
    ],
)
def test_inject_url_replaces_every_placeholder(template, url, expect):
    assert inject_url(template, url) == expect


def test_inject_url_is_marked_safe():
    result = inject_url("<div>[[url]]</div>", "/test/")

    assert result == "<div>/test/</div>"
    assert isinstance(result, SafeString)
