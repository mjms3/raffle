# Generated by Django 3.1.3 on 2020-11-11 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='raffleevent',
            name='name',
            field=models.CharField(max_length=250, unique=True),
        ),
    ]
