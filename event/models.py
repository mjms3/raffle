from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _
from private_files import PrivateFileField

from event.functions import file_visible_condition, _get_pixelated_image
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


class Gift(models.Model):
    add_ts = models.DateTimeField(default=datetime.now, blank=True)
    description = models.CharField(max_length=120)
    wrapped = models.BooleanField(default=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, editable=False, related_name='donations')
    given_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, blank=True, null=True, related_name='prizes')
    image = PrivateFileField(condition=file_visible_condition)
    pixelated_image = models.ImageField(editable=False)
    event = models.ForeignKey(RaffleEvent, on_delete=CASCADE)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.pixelated_image = _get_pixelated_image(self.image)
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
        if self.action_type == Action.ActionType.CHOOSE_GIFT:
            return '{:%H:%M:%S}: {} unwrapped a {}'.format(
                self.timestamp_ts,
                self.by_user,
                self.gift.description,
            )
        elif self.action_type == Action.ActionType.TRANSFERRED:
            return '{:%H:%m:%s}: {} transferred {} from {} to {}'.format(
                self.timestamp_ts,
                self.by_user,
                self.gift.description,
                self.from_user,
                self.to_user
            )
