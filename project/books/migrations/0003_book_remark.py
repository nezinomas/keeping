# Generated by Django 2.2.6 on 2019-10-18 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_auto_20190527_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='remark',
            field=models.TextField(blank=True, max_length=200),
        ),
    ]
