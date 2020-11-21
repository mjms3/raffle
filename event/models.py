import random
from datetime import datetime
from io import BytesIO
from os.path import splitext, basename

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CASCADE
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker

from custom_storages import MediaStorage
from raffle import settings


class RaffleEvent(models.Model):
    name = models.CharField(max_length=250, unique=True)

    class Phase(models.TextChoices):
        PRE_START = 'P', _('Pre Start')
        NORMAL_RAFFLE = 'N', _('Normal Raffle')
        GIFT_SWAP = 'G', _('Gift Swap')
        FINISHED = 'F', _('Finished')

    phase = models.CharField(max_length=1,choices=Phase.choices)
    current_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True, related_name='picking_in_raffles')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, through='RaffleParticipation')

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
        self._ensure_safe_to_modify()
        super().save(force_insert, force_update, using, update_fields)

    def full_clean(self, exclude=None, validate_unique=True):
        self._ensure_safe_to_modify()
        return super().full_clean(exclude, validate_unique)

    def _ensure_safe_to_modify(self):
        if self.event.phase == RaffleEvent.Phase.PRE_START and self.number_of_times_drawn != 0:
            raise Exception('Pre start and tickets have been drawn?!')
        elif self.event.phase == RaffleEvent.Phase.NORMAL_RAFFLE and self.tracker.has_changed('number_of_tickets'):
            raise Exception('Cant change number of available tickets during the raffle')
        elif self.event.phase in (RaffleEvent.Phase.GIFT_SWAP, RaffleEvent.Phase.FINISHED):
            raise Exception('Should not be updating details of raffle participation after raffle has finished')

    def __str__(self):
        return '%i tickets for %s in %s' % (self.number_of_tickets, self.user, self.event)


def file_visible_condition(request, instance):
    user_logged_in = (not request.user.is_anonymous) and request.user.is_authenticated
    owned_by_this_user = instance.added_by.pk == request.user.pk
    user_is_admin = request.user.is_superuser
    gift_is_unwrapped = not instance.wrapped
    return user_logged_in and (owned_by_this_user or user_is_admin or gift_is_unwrapped)


RESIZE_WIDTH = 600


def _process_image(image_obj):
    img = Image.open(BytesIO(image_obj.file.read()))

    width_percentage = RESIZE_WIDTH / float(img.size[0])
    horizontal_size = int((float(img.size[1]) * float(width_percentage)))
    img_shrunk = img.resize((RESIZE_WIDTH, horizontal_size), Image.ANTIALIAS)
    in_memory_file_for_normal_image = BytesIO()
    image_file_name, ext = splitext(image_obj.file.name)
    ext = ext.lstrip('.')

    img_shrunk.save(in_memory_file_for_normal_image, format=ext.lstrip('.'))

    img_small = img.resize((16, 16), resample=Image.BILINEAR)
    pixelated_image = img_small.resize(img.size, Image.NEAREST)

    in_memory_file_for_pixelated_image = BytesIO()
    pixelated_image.save(in_memory_file_for_pixelated_image, format=ext)
    now_str = datetime.now().strftime('%Y%m%d%H%M%S%f')
    return (
        ContentFile(in_memory_file_for_normal_image.getvalue(),
                    '{}/{}.{}'.format(now_str, hash(image_file_name), ext)),
        ContentFile(in_memory_file_for_pixelated_image.getvalue(),
                    '{}/pixelated-{}.{}'.format(now_str, image_file_name, ext)),
    )


def _pick_next_person(current_user, raffle_event):
    assert raffle_event.phase == RaffleEvent.Phase.NORMAL_RAFFLE
    raffle_participants = RaffleParticipation.objects.filter(event_id=raffle_event.id).filter(
        number_of_tickets__gt=F('number_of_times_drawn'))
    weights = [r.number_of_tickets - r.number_of_times_drawn for r in raffle_participants]
    next_person = random.choices(raffle_participants, weights)
    assert len(next_person) == 1, next_person
    next_person = next_person[0]
    action = Action(
        event=raffle_event,
        gift=None,
        from_user=None,
        to_user=next_person.user,
        by_user=current_user,
        action_type=Action.ActionType.CHANGED_USER
    )
    next_person.number_of_times_drawn += 1
    raffle_event.current_user = next_person.user
    raffle_event.save()
    action.save()
    next_person.save()

class Gift(models.Model):
    add_ts = models.DateTimeField(default=datetime.now, blank=True)
    description = models.CharField(max_length=120)
    wrapped = models.BooleanField(default=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, editable=False, related_name='donations')
    given_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, blank=True, null=True,
                                 related_name='prizes')
    image = models.ImageField(storage=MediaStorage)
    pixelated_image = models.ImageField(editable=False)
    event = models.ForeignKey(RaffleEvent, on_delete=CASCADE)

    tracker = FieldTracker(fields=('description',))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self._confirm_okay_to_change_model()

        self.image, self.pixelated_image = _process_image(self.image)
        super().save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        self._confirm_okay_to_change_model()
        return super().delete(using, keep_parents)

    def _confirm_okay_to_change_model(self):
        if self.event.phase != RaffleEvent.Phase.PRE_START and self.tracker.previous('description') is None:
            raise Exception("Can't add an item to the raffle after it has started")

    def __str__(self):
        return self.description

    @property
    def image_url(self):
        return self.pixelated_image.url if self.wrapped else self.image.url

    @property
    def image_id(self):
        return 'image-{}'.format(self.id)

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
