from datetime import datetime


def average(qs):
    now = datetime.now()
    arr = []

    for r in qs:
        year = r["year"]
        sum_val = float(r["sum"])

        cnt = now.month if year == now.year else 12

        arr.append(sum_val / cnt)

    return arr
