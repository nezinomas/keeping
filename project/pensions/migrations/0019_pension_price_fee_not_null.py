from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pensions", "0018_pensionbalance_sold_since_check"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pension",
            name="fee",
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name="pension",
            name="price",
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
    ]
