from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
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
    current_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return self.name


class RaffleParticipation(models.Model):
    event = models.ForeignKey(RaffleEvent, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    number_of_tickets = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    number_of_times_drawn = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    tracker = FieldTracker(fields=('number_of_tickets','number_of_times_drawn'))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'user'], name='event_user_uq')
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.event.phase == RaffleEvent.Phase.PRE_START and self.number_of_times_drawn!=0:
            raise Exception('Pre start and tickets have been drawn?!')
        elif self.event.phase == RaffleEvent.Phase.NORMAL_RAFFLE and self.tracker.has_changed('number_of_tickets'):
            raise Exception('Cant change number of available tickets during the raffle')
        elif self.event.phase in (RaffleEvent.Phase.GIFT_SWAP, RaffleEvent.Phase.FINISHED):
            raise Exception('Should not be updating details of raffle participation after raffle has finished')
        else:
            super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return 'Participation of %s in %s' %(self.user, self.event)


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
    gift = models.ForeignKey(Gift,on_delete=CASCADE, null=True)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='original_users', null=True)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='target_users')
    by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='acting_users')

    class ActionType(models.TextChoices):
        CHOOSE_GIFT = 'C', _('Chose gift')
        TRANSFERRED = 'T', _('Transferred')
        CHANGED_USER = 'U', _('Changed User')

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
            return '{:%H:%m:%S}: {} transferred {} from {} to {}'.format(
                self.timestamp_ts,
                self.by_user,
                self.gift.description,
                self.from_user,
                self.to_user
            )
        elif self.action_type == Action.ActionType.CHANGED_USER:
            return "{:%H:%m:%S}: It is {}'s turn to pick!".format(
                self.timestamp_ts,
                self.to_user
            )

    def __str__(self):
        return self.message
