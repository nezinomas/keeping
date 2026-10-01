import django.core.validators
from django.db import migrations, models
from django.utils.text import slugify

import project.core.validators


def fill_slugs(apps, schema_editor):
    saving_type = apps.get_model("savings", "SavingType")
    rows = list(saving_type.objects.all())
    for row in rows:
        row.slug = slugify(row.title)
    saving_type.objects.bulk_update(rows, ["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0003_alter_journal_title"),
        ("savings", "0016_alter_savingbalance_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="savingtype",
            name="title",
            field=models.CharField(
                max_length=50,
                validators=[
                    django.core.validators.MinLengthValidator(3),
                    project.core.validators.validate_title_slug,
                ],
            ),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="savingtype",
            constraint=models.UniqueConstraint(
                fields=("journal", "slug"), name="savings_savingtype_unique_slug"
            ),
        ),
    ]
