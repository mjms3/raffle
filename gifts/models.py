from datetime import datetime
from io import BytesIO
from os.path import join, dirname, basename, splitext

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models


class Gift(models.Model):
    add_ts = models.DateTimeField(default=datetime.now, blank=True)
    description = models.TextField()
    wrapped = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    image = models.ImageField()
    pixelated_image = models.ImageField(editable=False)

    def _get_pixelated_image(self):
        image_path = self.image.path
        img = Image.open(BytesIO(self.image.file.read()))
        img_small = img.resize((16, 16), resample=Image.BILINEAR)
        result = img_small.resize(img.size, Image.NEAREST)
        _, ext = splitext(image_path)
        in_memory_file = BytesIO()
        result.save(in_memory_file, format=ext.lstrip('.'))
        new_path = join(dirname(image_path), 'pixelated-{}'.format(basename(image_path)))
        self.pixelated_image = ContentFile(in_memory_file.getvalue(), new_path)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self._get_pixelated_image()
        super().save(force_insert, force_update, using, update_fields)
