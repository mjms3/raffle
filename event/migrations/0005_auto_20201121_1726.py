# Generated by Django 3.1.3 on 2020-11-21 17:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('event', '0004_auto_20201111_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='raffleevent',
            name='participants',
            field=models.ManyToManyField(through='event.RaffleParticipation', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='gift',
            name='image',
            field=models.ImageField(upload_to=''),
        ),
        migrations.AlterField(
            model_name='raffleevent',
            name='current_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='picking_in_raffles', to=settings.AUTH_USER_MODEL),
        ),
    ]