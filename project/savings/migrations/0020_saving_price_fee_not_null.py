from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0019_savingbalance_sold_since_check"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saving",
            name="fee",
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name="saving",
            name="price",
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
    ]
