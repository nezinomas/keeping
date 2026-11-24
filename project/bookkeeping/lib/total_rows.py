from ...core.lib.money_cells import rounds_to_zero


def total_row(data, fields: list[str]) -> dict:
    """Each of `fields` summed over the rows; a row without one raises KeyError."""
    row = dict.fromkeys(fields, 0)

    for obj in data:
        values = obj.__dict__
        for field in fields:
            row[field] += values[field]

    return row


def funds_total_row(data, fields: list[str], switched_within: int = 0) -> dict:
    """The funds tables' Total row: profit and % read only the rows showing one."""
    row = total_row(data, [f for f in fields if f != "profit_proc"])
    shown = [obj for obj in data if obj.shows_profit]
    shown_row = total_row(shown, ["incomes", "profit_sum"])
    row["profit_sum"] = shown_row["profit_sum"]
    row["profit_proc"] = profit_percent(shown_row, switched_within)
    row["profit_proc_signed"] = not rounds_to_zero(row["profit_proc"])
    return row


def profit_percent(row: dict, switched_within: int = 0) -> float:
    base = row["incomes"] - switched_within
    if base <= 0:
        return 0.0

    return row["profit_sum"] / base * 100
