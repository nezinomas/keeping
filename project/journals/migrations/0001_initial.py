# Generated by Django 4.0.4 on 2022-05-19 13:41

import datetime

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Journal",
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
                    "title",
                    models.CharField(
                        max_length=25,
                        validators=[django.core.validators.MinLengthValidator(3)],
                    ),
                ),
                ("slug", models.SlugField(editable=False, max_length=25)),
                (
                    "first_record",
                    models.DateField(default=datetime.date.today, editable=False),
                ),
                (
                    "unnecessary_expenses",
                    models.CharField(blank=True, max_length=254, null=True),
                ),
                ("unnecessary_savings", models.BooleanField(default=False)),
                ("lang", models.CharField(default="en", max_length=2)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
