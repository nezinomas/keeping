from datetime import date, timedelta

from ...lib.rhythm import EmptyGap, Rhythm


def _records(*dates, quantity=1.0):
    return [{"date": d, "quantity": quantity} for d in dates]


def test_two_records_five_days_apart_make_one_gap_of_five():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 1, 6)))

    assert [gap.days for gap in rhythm.gaps] == [5]


def test_records_on_consecutive_days_make_a_gap_of_one():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 1, 2)))

    assert [gap.days for gap in rhythm.gaps] == [1]


def test_two_records_on_one_day_make_a_gap_of_zero():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 1, 1)))

    assert [gap.days for gap in rhythm.gaps] == [0]


def test_a_gap_is_bounded_by_the_records_at_its_ends():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 1, 6)))
    gap = rhythm.gaps[0]

    assert gap.dates == (date(1999, 1, 1), date(1999, 1, 6))
    assert gap.label == "1999-01-01 → 1999-01-06"


def test_the_first_record_opens_no_gap_of_its_own():
    rhythm = Rhythm(_records(date(1999, 3, 1), date(1999, 3, 8)))

    assert len(rhythm.gaps) == 1


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


def test_a_counter_with_one_record_has_no_gap():
    rhythm = Rhythm(_records(date(1999, 1, 1)))

    assert rhythm.gaps == []
    assert isinstance(rhythm.typical_gap, EmptyGap)
    assert rhythm.typical_gap.days == 0
    assert rhythm.typical_gap.dates == ()
    assert rhythm.typical_gap.label == ""


def test_a_counter_with_no_records_has_no_gap():
    rhythm = Rhythm([])

    assert rhythm.gaps == []
    assert isinstance(rhythm.typical_gap, EmptyGap)


def test_total_ever_sums_every_quantity():
    rhythm = Rhythm(
        [
            {"date": date(1998, 1, 1), "quantity": 2.0},
            {"date": date(1999, 1, 1), "quantity": 3.0},
        ]
    )

    assert rhythm.total_ever == 5.0


def test_total_ever_of_a_counter_with_no_records_is_zero():
    assert Rhythm([]).total_ever == 0.0


def test_rate_divides_by_the_span_between_the_first_and_last_record():
    rhythm = Rhythm(_records(date(1999, 1, 1), date(1999, 2, 1), date(1999, 4, 1)))

    assert round(rhythm.rate, 1) == 12.2


def test_rate_of_a_counter_with_a_single_record_is_zero():
    assert Rhythm(_records(date(1999, 1, 1))).rate == 0.0


def test_current_gap_counts_the_days_since_the_last_record():
    rhythm = Rhythm(_records(date(1999, 1, 1)), today=date(1999, 1, 11))

    assert rhythm.current_gap == 10


def test_current_gap_of_a_counter_with_no_records_is_zero():
    assert Rhythm([], today=date(1999, 1, 11)).current_gap == 0


# -------------------------------------------------------------------------------------
#                                                            Read against a Counter year
# -------------------------------------------------------------------------------------
def test_the_first_gap_of_a_year_reaches_back_to_the_year_before():
    rhythm = Rhythm(
        _records(date(1998, 12, 22), date(1999, 1, 1), date(1999, 1, 3)), year=1999
    )

    assert [gap.days for gap in rhythm.year_gaps] == [10, 2]


def test_a_single_record_in_a_year_gives_no_completed_gap():
    rhythm = Rhythm(_records(date(1999, 5, 1)), year=1999)

    assert rhythm.year_gaps == []
    assert isinstance(rhythm.year_median_gap, EmptyGap)


def test_the_current_gap_enters_neither_the_years_longest_nor_its_median():
    rhythm = Rhythm(
        _records(date(1999, 1, 1), date(1999, 1, 3)),
        today=date(1999, 12, 31),
        year=1999,
    )

    assert rhythm.current_gap == 362
    assert rhythm.year_median_gap.days == 2
    assert rhythm.longest_gap.days == 2


def test_an_empty_year_returns_the_empty_variants():
    rhythm = Rhythm(_records(date(1998, 1, 1), date(1998, 1, 5)), year=1999)

    assert rhythm.year_gaps == []
    assert isinstance(rhythm.year_median_gap, EmptyGap)
    assert rhythm.year_records == 0


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


def test_a_bin_holding_one_length_labels_that_length_alone():
    assert Rhythm(_spaced([7, 7, 7])).gap_distribution[0].label == "7"


def test_a_bin_spanning_lengths_labels_both_ends():
    assert Rhythm(_spaced(SPARSE)).gap_distribution[0].label == "59–69"


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


def test_a_dense_counters_cluster_does_not_collapse_into_one_bin():
    bins = Rhythm(_spaced(DENSE)).gap_distribution

    assert len([x for x in bins if x.low <= 14 and x.high >= 4]) >= 3
