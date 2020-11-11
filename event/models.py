from datetime import datetime
from io import BytesIO
from os.path import basename, splitext

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _
from private_files import PrivateFileField

from raffle import settings


class RaffleEvent(models.Model):
    name = models.CharField(max_length=250, unique=True)

    class Phase(models.TextChoices):
        PRE_START = 'P', _('Pre Start')
        NORMAL_RAFFLE = 'N', _('Normal Raffle')
        GIFT_SWAP = 'G', _('Gift Swap')
        FINISHED = 'F', _('Finished')

    phase = models.CharField(max_length=1,choices=Phase.choices)

    def __str__(self):
        return self.name

class RaffleParticipation(models.Model):
    event = models.ForeignKey(RaffleEvent, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    number_of_tickets = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'user'], name='event_user_uq')
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        assert self.event.phase == RaffleEvent.Phase.PRE_START, 'Can not update participation in a raffle after it has started'
        super().save(force_insert, force_update, using, update_fields)


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
    event = models.ForeignKey(RaffleEvent, on_delete=CASCADE)

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

    def __str__(self):
        return self.description

class Action(models.Model):
    event = models.ForeignKey(RaffleEvent, on_delete=CASCADE)
    timestamp_ts = models.DateTimeField(auto_now_add=True, blank=True)
    gift = models.ForeignKey(Gift,on_delete=CASCADE)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='original_users')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='target_users')
    by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='acting_users')

    class ActionType(models.TextChoices):
        CHOOSE_GIFT = 'C', _('Chose gift')
        TRANSFERRED = 'T', _('Transferred')

    action_type = models.CharField(max_length=1, choices=ActionType.choices)

    @property
    def message(self):
        if self.action_type == self.ActionType.CHOOSE_GIFT:
            return '{:%H:%M:%S}: {} unwrapped a {}'.format(
                self.timestamp_ts,
                self.by_user,
                self.gift.description,
            )
        elif self.action_type == self.ActionType.TRANSFERRED:
            return '{:%H:%m:%s}: {} transferred {} from {} to {}'.format(
                self.timestamp_ts,
                self.by_user,
                self.gift.description,
                self.from_user,
                self.to_user
            )
