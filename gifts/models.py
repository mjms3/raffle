from datetime import datetime
from io import BytesIO
from os.path import basename, splitext

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from private_files import PrivateFileField

from raffle import settings


def file_visible_condition(request, instance):
    user_logged_in = (not request.user.is_anonymous) and request.user.is_authenticated
    owned_by_this_user = instance.added_by.pk == request.user.pk
    user_is_admin = request.user.is_superuser
    gift_is_unwrapped = not instance.wrapped
    return user_logged_in and (owned_by_this_user or user_is_admin or gift_is_unwrapped)

class Gift(models.Model):
    add_ts = models.DateTimeField(default=datetime.now, blank=True)
    description = models.CharField(max_length=120)
    wrapped = models.BooleanField(default=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, editable=False, related_name='donations')
    given_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, blank=True, null=True, related_name='prizes')
    image = PrivateFileField(condition=file_visible_condition)
    pixelated_image = models.ImageField(editable=False)

    def _get_pixelated_image(self):
        image_path = self.image.path
        img = Image.open(BytesIO(self.image.file.read()))
        img_small = img.resize((16, 16), resample=Image.BILINEAR)
        result = img_small.resize(img.size, Image.NEAREST)
        _, ext = splitext(image_path)
        in_memory_file = BytesIO()
        result.save(in_memory_file, format=ext.lstrip('.'))
        self.pixelated_image = ContentFile(in_memory_file.getvalue(), 'pixelated-{}'.format(basename(image_path)))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self._get_pixelated_image()
        super().save(force_insert, force_update, using, update_fields)
