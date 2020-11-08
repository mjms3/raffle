# Generated by Django 3.1.3 on 2020-11-08 13:12

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Gift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('add_ts', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('description', models.TextField()),
                ('wrapped', models.BooleanField(default=True)),
                ('image', models.ImageField(upload_to='')),
                ('pixelated_image', models.ImageField(editable=False, upload_to='')),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
