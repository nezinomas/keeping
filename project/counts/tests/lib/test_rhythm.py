from datetime import date

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
