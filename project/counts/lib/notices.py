"""Which empty state a Counts page is in. The template maps a state to a
sentence and owns the markup in it."""

NO_COUNTERS = "no_counters"
NO_RECORDS = "no_records"
EMPTY_YEAR = "empty_year"


def notice_state(has_records: bool, has_year_records: bool) -> str:
    if not has_records:
        return NO_RECORDS

    if not has_year_records:
        return EMPTY_YEAR

    return ""
