# Generated by Django 3.2.6 on 2021-08-12 13:15

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=25)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['title'],
                'unique_together': {('user', 'title')},
            },
        ),
    ]
