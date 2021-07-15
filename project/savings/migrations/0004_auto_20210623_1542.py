# Generated by Django 3.2.3 on 2021-06-23 12:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0001_initial'),
        ('savings', '0003_auto_20200123_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingtype',
            name='journal',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='saving_types', to='journals.journal'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='savingtype',
            unique_together={('journal', 'title')},
        ),
        migrations.RemoveField(
            model_name='savingtype',
            name='user',
        ),
    ]
