import string

from hypothesis import example, given
from hypothesis import strategies as st

from ...templatetags import template_filters

WEEKDAYS = st.integers(0, 6)


@given(
    value=st.one_of(WEEKDAYS, WEEKDAYS.map(str), st.just("")),
    css_class=st.text(string.ascii_letters, min_size=1),
)
@example(value="0", css_class="X")  # sunday
@example(value=0, css_class="X")
@example(value="6", css_class="X")  # saturday
@example(value=6, css_class="X")
@example(value="1", css_class="X")
@example(value=1, css_class="X")
@example(value="", css_class="X")
def test_weekend_gives_its_class_to_saturday_and_sunday_only(value, css_class):
    actual = template_filters.weekend(value, css_class)

    assert actual == (css_class if str(value) in {"0", "6"} else "")
