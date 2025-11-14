def total_row(data, fields: list[str]) -> dict:
    # Fields to subtract when sold is truthy
    subtract_fields = {"incomes", "profit_sum"}

    # Initialize result dictionary
    row = {field: 0 for field in fields}

    # Process each object
    for obj in data:
        # Get all field values in one pass
        values = obj.__dict__
        sold = values.get("sold", 0)

        # Update sums for all fields
        for field in fields:
            if field in subtract_fields and sold:
                continue

            value = values.get(field, 0)
            row[field] += value

    # Update profit_proc if applicable
    if "profit_proc" in fields and row.get("market_value"):
        row["profit_proc"] = calculate_percents(row)

    return row


def calculate_percents(data):
    incomes = data.get("incomes", 0)
    fee = data.get("fee", 0)
    market_value = data.get("market_value", 0)

    return ((market_value - fee) / incomes * 100) - 100 if incomes else 0
