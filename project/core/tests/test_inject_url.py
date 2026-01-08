from django.utils.safestring import SafeString
from ..templatetags.fast_rendering import inject_url


def test_inject_url_success():
    """It should replace the placeholder with the given URL."""
    template = '<a href="[[url]]">Edit</a>'
    url = "/expenses/update/123/"

    result = inject_url(template, url)

    assert result == '<a href="/expenses/update/123/">Edit</a>'


def test_inject_url_is_marked_safe():
    """The result must be a SafeString so Django does not escape the HTML tags."""
    template = "<div>[[url]]</div>"
    result = inject_url(template, "/test/")

    assert result == "<div>/test/</div>"
    assert isinstance(result, SafeString)


def test_inject_url_multiple_occurrences():
    """It should replace ALL instances of the placeholder."""
    # Scenario: using the URL in href and also in a data attribute
    template = '<a href="[[url]]" data-hx-get="[[url]]">Link</a>'
    url = "/foo/bar/"

    result = inject_url(template, url)

    assert result == '<a href="/foo/bar/" data-hx-get="/foo/bar/">Link</a>'


def test_inject_url_no_placeholder():
    """It should return the original string if placeholder is missing."""
    template = "<span>No link here</span>"
    url = "/somewhere/"

    result = inject_url(template, url)

    assert result == "<span>No link here</span>"


def test_inject_url_empty_template():
    """It should return an empty string if template is None or empty."""
    assert inject_url("", "/url/") == ""
    assert inject_url(None, "/url/") == ""


def test_inject_url_handles_non_string_url():
    """It should cast integers or other types to string automatically."""
    template = "ID: [[url]]"

    # Passing an integer 123 instead of string "123"
    result = inject_url(template, 123)

    assert result == "ID: 123"
