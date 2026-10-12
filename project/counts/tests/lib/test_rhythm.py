from datetime import date, timedelta

import pytest

from ...lib.rhythm import EmptyGap, Rhythm


def _records(*dates, quantity=1.0):
    return [{"date": d, "qty": quantity} for d in dates]


@pytest.mark.parametrize(
    "second, expected",
    [
        pytest.param(date(1999, 1, 6), 5, id="five_days_apart"),
        pytest.param(date(1999, 1, 2), 1, id="consecutive_days"),
        pytest.param(date(1999, 1, 1), 0, id="one_day"),
    ],
)
def test_two_records_make_one_gap_of_the_days_between_them(second, expected):
    rhythm = Rhythm(_records(date(1999, 1, 1), second))

    assert [gap.days for gap in rhythm.gaps] == [expected]


def test_a_gap_is_bounded_by_the_records_at_its_ends():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 1, 6)))
    gap = rhythm.gaps[0]

    assert gap.dates == (date(1999, 1, 1), date(1999, 1, 6))
    assert gap.label == "1999-01-01 → 1999-01-06"


def test_typical_gap_is_the_median_of_every_gap():
    rhythm = Rhythm(
        _records(
            date(1999, 1, 1),
            date(1999, 1, 3),
            date(1999, 1, 13),
            date(1999, 1, 16),
        )
    )

    assert [gap.days for gap in rhythm.gaps] == [2, 10, 3]
    assert rhythm.typical_gap.days == 3


def test_typical_gap_of_an_even_count_of_gaps_averages_the_middle_pair():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 1, 3), date(1999, 1, 13)))

    assert [gap.days for gap in rhythm.gaps] == [2, 10]
    assert rhythm.typical_gap.days == 6


def test_the_current_gap_never_enters_the_typical_gap():
    rhythm = Rhythm(
        _records(date(1999, 1, 1), date(1999, 1, 3)), today=date(1999, 12, 31)
    )

    assert rhythm.current_gap == 362
    assert rhythm.typical_gap.days == 2


@pytest.mark.parametrize(
    "records",
    [
        pytest.param(_records(date(1999, 1, 1)), id="one_record"),
        pytest.param([], id="no_records"),
    ],
)
def test_a_counter_with_fewer_than_two_records_has_no_gap(records):
    rhythm = Rhythm(records)

    assert rhythm.gaps == []
    assert isinstance(rhythm.typical_gap, EmptyGap)
    assert rhythm.typical_gap.days == 0
    assert rhythm.typical_gap.dates == ()
    assert rhythm.typical_gap.label == ""


@pytest.mark.parametrize(
    "records, expect",
    [
        pytest.param(
            [
                {"date": date(1998, 1, 1), "qty": 2.0},
                {"date": date(1999, 1, 1), "qty": 3.0},
            ],
            5.0,
            id="sums_every_quantity",
        ),
        pytest.param([], 0.0, id="no_records"),
    ],
)
def test_total_ever(records, expect):
    assert Rhythm(records).total_ever == expect


@pytest.mark.parametrize(
    "records, expect",
    [
        pytest.param(
            _records(date(1999, 1, 1), date(1999, 2, 1), date(1999, 4, 1)),
            12.2,
            id="span_between_first_and_last",
        ),
        pytest.param(_records(date(1999, 1, 1)), 0.0, id="single_record"),
    ],
)
def test_rate_divides_by_the_span_between_the_first_and_last_record(records, expect):
    assert round(Rhythm(records).rate, 1) == expect


@pytest.mark.parametrize(
    "records, expect",
    [
        pytest.param(_records(date(1999, 1, 1)), 10, id="days_since_the_last_record"),
        pytest.param([], 0, id="no_records"),
    ],
)
def test_current_gap(records, expect):
    assert Rhythm(records, today=date(1999, 1, 11)).current_gap == expect


def test_the_first_gap_of_a_year_reaches_back_to_the_year_before():
    rhythm = Rhythm(
        _records(date(1998, 12, 22), date(1999, 1, 1), date(1999, 1, 3)), year=1999
    )

    assert [gap.days for gap in rhythm.year_gaps] == [10, 2]


def test_the_current_gap_enters_neither_the_years_longest_nor_its_median():
    rhythm = Rhythm(
        _records(date(1999, 1, 1), date(1999, 1, 3)),
        today=date(1999, 12, 31),
        year=1999,
    )

    assert rhythm.current_gap == 362
    assert rhythm.year_median_gap.days == 2
    assert rhythm.longest_gap.days == 2


@pytest.mark.parametrize(
    "records, year_records",
    [
        pytest.param(_records(date(1999, 5, 1)), 1, id="single_record_in_the_year"),
        pytest.param(_records(date(1998, 1, 1), date(1998, 1, 5)), 0, id="empty_year"),
    ],
)
def test_a_year_without_a_completed_gap_returns_the_empty_variants(
    records, year_records
):
    rhythm = Rhythm(records, year=1999)

    assert rhythm.year_gaps == []
    assert isinstance(rhythm.year_median_gap, EmptyGap)
    assert rhythm.year_records == year_records


def test_the_years_median_and_the_typical_gap_read_different_sets():
    rhythm = Rhythm(
        _records(
            date(1997, 1, 1),
            date(1997, 1, 3),
            date(1997, 1, 5),
            date(1999, 1, 1),
            date(1999, 3, 1),
        ),
        year=1999,
    )

    assert [gap.days for gap in rhythm.gaps] == [2, 2, 726, 59]
    assert rhythm.year_median_gap.days == 392.5
    assert rhythm.typical_gap.days == 30.5


def test_year_records_counts_the_records_of_the_year_on_view():
    rhythm = Rhythm(
        _records(date(1998, 1, 1), date(1999, 1, 1), date(1999, 6, 1)), year=1999
    )

    assert rhythm.year_records == 2


def test_the_longest_gap_names_the_records_at_its_ends():
    rhythm = Rhythm(
        _records(date(1999, 1, 1), date(1999, 1, 3), date(1999, 5, 1)), year=1999
    )

    assert rhythm.longest_gap.days == 118
    assert rhythm.longest_gap.label == "1999-01-03 → 1999-05-01"


def test_a_counter_with_one_record_has_no_longest_gap():
    rhythm = Rhythm(_records(date(1999, 1, 1)), year=1999)

    assert isinstance(rhythm.longest_gap, EmptyGap)


# the two shapes the bins must serve at once: a repeated length, and a low cluster
SPARSE = [59, 63, 63, 63, 63, 63, 63, 66, 68, 73, 81, 87, 98, 119, 143, 167, 189, 229]
DENSE = [
    4,
    5,
    5,
    6,
    6,
    6,
    7,
    7,
    7,
    8,
    8,
    8,
    9,
    9,
    9,
    10,
    10,
    11,
    11,
    12,
    12,
    13,
    14,
    14,
    17,
    19,
    21,
    26,
    30,
    40,
    58,
]


def _spaced(gaps):
    day = date(1999, 1, 1)
    dates = [day]
    for gap in gaps:
        day += timedelta(days=gap)
        dates.append(day)

    return _records(*dates)


def test_a_counter_with_no_records_has_no_gap_distribution():
    assert Rhythm([]).gap_distribution == []


def test_gaps_all_of_one_length_make_a_single_bin():
    bins = Rhythm(_spaced([7, 7, 7])).gap_distribution

    assert [(x.low, x.high, x.count) for x in bins] == [(7, 7, 3)]


@pytest.mark.parametrize(
    "gaps, label",
    [
        pytest.param([7, 7, 7], "7", id="one_length_alone"),
        pytest.param(SPARSE, "59–69", id="both_ends"),
    ],
)
def test_a_bin_labels_the_lengths_it_holds(gaps, label):
    assert Rhythm(_spaced(gaps)).gap_distribution[0].label == label


def test_every_gap_lands_in_exactly_one_bin():
    bins = Rhythm(_spaced(DENSE)).gap_distribution

    assert sum(x.count for x in bins) == len(DENSE)


def test_the_bins_run_from_the_shortest_gap_to_the_longest():
    bins = Rhythm(_spaced(DENSE)).gap_distribution

    assert bins[0].low == min(DENSE)
    assert bins[-1].high == max(DENSE)


def test_the_edges_come_from_the_counters_own_gaps():
    sparse = Rhythm(_spaced(SPARSE)).gap_distribution
    dense = Rhythm(_spaced(DENSE)).gap_distribution

    assert (sparse[0].low, sparse[-1].high) != (dense[0].low, dense[-1].high)


def test_a_sparse_counters_repeated_length_stands_out_as_one_bar():
    bins = Rhythm(_spaced(SPARSE)).gap_distribution
    tallest = max(bins, key=lambda x: x.count)
    runner_up = sorted(x.count for x in bins)[-2]

    assert tallest.low <= 63 <= tallest.high
    assert tallest.count > 2 * runner_up


def test_edges_that_round_to_one_another_leave_no_inverted_or_skipped_bin():
    bins = Rhythm(_spaced([1, 2, 3])).gap_distribution

    assert all(x.low <= x.high for x in bins)
    assert [b.low for b in bins[1:]] == [a.high + 1 for a in bins[:-1]]


def test_a_dense_counters_cluster_does_not_collapse_into_one_bin():
    bins = Rhythm(_spaced(DENSE)).gap_distribution

    assert len([x for x in bins if x.low <= 14 and x.high >= 4]) >= 3
