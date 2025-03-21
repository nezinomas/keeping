# Generated by Django 4.0.4 on 2022-05-19 13:41

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("journals", "0001_initial"),
        ("incomes", "0001_initial"),
        ("savings", "0001_initial"),
        ("expenses", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SavingPlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "january",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "february",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "march",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "april",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "may",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "june",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "july",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "august",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "september",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "october",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "november",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "december",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1974),
                            django.core.validators.MaxValueValidator(2050),
                        ]
                    ),
                ),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saving_plans",
                        to="journals.journal",
                    ),
                ),
                (
                    "saving_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="savings.savingtype",
                    ),
                ),
            ],
            options={
                "ordering": ["saving_type"],
                "unique_together": {("year", "saving_type", "journal")},
            },
        ),
        migrations.CreateModel(
            name="NecessaryPlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "january",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "february",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "march",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "april",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "may",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "june",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "july",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "august",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "september",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "october",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "november",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "december",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1974),
                            django.core.validators.MaxValueValidator(2050),
                        ]
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="necessary_plans",
                        to="journals.journal",
                    ),
                ),
            ],
            options={
                "ordering": ["year", "title"],
                "unique_together": {("year", "title", "journal")},
            },
        ),
        migrations.CreateModel(
            name="IncomePlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "january",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "february",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "march",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "april",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "may",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "june",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "july",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "august",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "september",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "october",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "november",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "december",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1974),
                            django.core.validators.MaxValueValidator(2050),
                        ]
                    ),
                ),
                (
                    "income_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="incomes.incometype",
                    ),
                ),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="income_plans",
                        to="journals.journal",
                    ),
                ),
            ],
            options={
                "ordering": ["income_type"],
                "unique_together": {("year", "income_type", "journal")},
            },
        ),
        migrations.CreateModel(
            name="ExpensePlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "january",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "february",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "march",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "april",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "may",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "june",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "july",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "august",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "september",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "october",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "november",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "december",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1974),
                            django.core.validators.MaxValueValidator(2050),
                        ]
                    ),
                ),
                (
                    "expense_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="expenses.expensetype",
                    ),
                ),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="expense_plans",
                        to="journals.journal",
                    ),
                ),
            ],
            options={
                "ordering": ["expense_type"],
                "unique_together": {("year", "expense_type", "journal")},
            },
        ),
        migrations.CreateModel(
            name="DayPlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "january",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "february",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "march",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "april",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "may",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "june",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "july",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "august",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "september",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "october",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "november",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "december",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1974),
                            django.core.validators.MaxValueValidator(2050),
                        ]
                    ),
                ),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="day_plans",
                        to="journals.journal",
                    ),
                ),
            ],
            options={
                "ordering": ["year"],
                "unique_together": {("year", "journal")},
            },
        ),
    ]
