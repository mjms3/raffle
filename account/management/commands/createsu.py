import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        userModel = get_user_model()
        if not userModel.objects.filter(username="admin").exists():
            userModel.objects.create_superuser("admin", "admin@admin.com", os.environ['SU_PASSWORD'])
