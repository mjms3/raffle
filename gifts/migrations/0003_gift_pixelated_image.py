# Generated by Django 3.1.2 on 2020-11-01 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gifts', '0002_auto_20201101_1417'),
    ]

    operations = [
        migrations.AddField(
            model_name='gift',
            name='pixelated_image',
            field=models.ImageField(default='/asdf', editable=False, upload_to=''),
            preserve_default=False,
        ),
    ]
