from dataclasses import replace

from ..lib.calc_day_sum import DataDto

MONTH_LEN = [
    {"month": 1, "amount": 31},
    {"month": 2, "amount": 29},
    {"month": 3, "amount": 31},
    {"month": 4, "amount": 30},
    {"month": 5, "amount": 31},
    {"month": 6, "amount": 30},
    {"month": 7, "amount": 31},
    {"month": 8, "amount": 31},
    {"month": 9, "amount": 30},
    {"month": 10, "amount": 31},
    {"month": 11, "amount": 30},
    {"month": 12, "amount": 31},
]


def make_data(**changes):
    data = DataDto(
        incomes=[
            {"month": 1, "amount": 900},
            {"month": 2, "amount": 1000},
            {"month": 3, "amount": 450},
            {"month": 4, "amount": 450},
            {"month": 5, "amount": 450},
            {"month": 6, "amount": 450},
            {"month": 7, "amount": 450},
            {"month": 8, "amount": 450},
            {"month": 9, "amount": 450},
            {"month": 10, "amount": 450},
            {"month": 11, "amount": 450},
            {"month": 12, "amount": 450},
        ],
        expenses_regular=[
            {"month": 1, "amount": 260},
            {"month": 2, "amount": 280},
        ],
        expenses_necessary=[
            {"month": 1, "amount": 300},
            {"month": 2, "amount": 320},
        ],
        savings=[
            {"month": 1, "amount": 190},
            {"month": 2, "amount": 200},
        ],
        per_day=[
            {"month": 1, "amount": 25},
            {"month": 2, "amount": 26},
        ],
        necessary=[
            {"month": 2, "amount": 100},
        ],
        month_len=MONTH_LEN,
    )

    return replace(data, **changes)
