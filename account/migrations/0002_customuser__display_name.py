# Generated by Django 3.1.3 on 2020-12-07 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='_display_name',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='display name'),
        ),
    ]
