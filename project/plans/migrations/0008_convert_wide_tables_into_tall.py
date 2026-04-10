from django.db import migrations

MONTH_NAMES = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def convert_wide_to_tall(apps, schema_editor):
    # Load all models
    IncomePlan = apps.get_model("plans", "IncomePlan")
    ExpensePlan = apps.get_model("plans", "ExpensePlan")
    SavingPlan = apps.get_model("plans", "SavingPlan")
    DayPlan = apps.get_model("plans", "DayPlan")
    NecessaryPlan = apps.get_model("plans", "NecessaryPlan")

    # --- 1. Income Plans ---
    new_incomes = []
    incomes_to_delete = []
    for plan in IncomePlan.objects.all():
        for idx, month_name in enumerate(MONTH_NAMES, start=1):
            price = getattr(plan, month_name)
            if price is not None:
                new_incomes.append(
                    IncomePlan(
                        year=plan.year,
                        month=idx,
                        price=price,
                        income_type=plan.income_type,
                        journal=plan.journal,
                    )
                )
        incomes_to_delete.append(plan.id)
    IncomePlan.objects.filter(id__in=incomes_to_delete).delete()
    IncomePlan.objects.bulk_create(new_incomes)

    # --- 2. Expense Plans ---
    new_expenses = []
    expenses_to_delete = []
    for plan in ExpensePlan.objects.all():
        for idx, month_name in enumerate(MONTH_NAMES, start=1):
            price = getattr(plan, month_name)
            if price is not None:
                new_expenses.append(
                    ExpensePlan(
                        year=plan.year,
                        month=idx,
                        price=price,
                        expense_type=plan.expense_type,
                        journal=plan.journal,
                    )
                )
        expenses_to_delete.append(plan.id)
    ExpensePlan.objects.filter(id__in=expenses_to_delete).delete()
    ExpensePlan.objects.bulk_create(new_expenses)

    # --- 3. Saving Plans ---
    new_savings = []
    savings_to_delete = []
    for plan in SavingPlan.objects.all():
        for idx, month_name in enumerate(MONTH_NAMES, start=1):
            price = getattr(plan, month_name)
            if price is not None:
                new_savings.append(
                    SavingPlan(
                        year=plan.year,
                        month=idx,
                        price=price,
                        saving_type=plan.saving_type,
                        journal=plan.journal,
                    )
                )
        savings_to_delete.append(plan.id)
    SavingPlan.objects.filter(id__in=savings_to_delete).delete()
    SavingPlan.objects.bulk_create(new_savings)

    # --- 4. Day Plans ---
    new_days = []
    days_to_delete = []
    for plan in DayPlan.objects.all():
        for idx, month_name in enumerate(MONTH_NAMES, start=1):
            price = getattr(plan, month_name)
            if price is not None:
                new_days.append(
                    DayPlan(
                        year=plan.year, month=idx, price=price, journal=plan.journal
                    )
                )
        days_to_delete.append(plan.id)
    DayPlan.objects.filter(id__in=days_to_delete).delete()
    DayPlan.objects.bulk_create(new_days)

    # --- 5. Necessary Plans ---
    new_necessary = []
    necessary_to_delete = []
    for plan in NecessaryPlan.objects.all():
        for idx, month_name in enumerate(MONTH_NAMES, start=1):
            price = getattr(plan, month_name)
            if price is not None:
                new_necessary.append(
                    NecessaryPlan(
                        year=plan.year,
                        month=idx,
                        price=price,
                        title=plan.title,
                        expense_type=plan.expense_type,
                        journal=plan.journal,
                    )
                )
        necessary_to_delete.append(plan.id)
    NecessaryPlan.objects.filter(id__in=necessary_to_delete).delete()
    NecessaryPlan.objects.bulk_create(new_necessary)


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0006_alter_necessaryplan_options_and_more"),
    ]

    operations = [
        migrations.RunPython(
            convert_wide_to_tall, reverse_code=migrations.RunPython.noop
        ),
    ]
