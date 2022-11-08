from datetime import datetime
from typing import List

from ...expenses.models import ExpenseType


def expense_types(*args: str) -> List[str]:
    qs = (
        ExpenseType
        .objects
        .items()
        .values_list('title', flat=True)
    )

    arr = list(qs) + list(args)
    arr.sort()

    return arr


def average(qs):
    now = datetime.now()
    arr = []

    for r in qs:
        year = r['year']
        sum_val = float(r['sum'])

        cnt = now.month if year == now.year else 12

        arr.append(sum_val / cnt)

    return arr


def add_latest_check_key(worth_data, balance_data):
    if worth_data:
        for row in balance_data:
            latest = [x['latest_check'] for x in worth_data if x.get('title') == row['title']]
            row['latest_check'] = latest[0] if latest else None

    return balance_data
