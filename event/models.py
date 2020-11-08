from django.db import models
from django.db.models import CASCADE

from gifts.models import Gift
from raffle import settings
from django.utils.translation import gettext_lazy as _

class Action(models.Model):
    gift_id = models.ForeignKey(Gift,on_delete=CASCADE)
    from_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='original_users')
    to_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='target_users')
    by_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='acting_users')

    class ActionType(models.TextChoices):
        CHOOSE_GIFT = 'C', _('Chose gift')
        TRANSFERRED = 'T', _('Transferred')

    action_type = models.CharField(max_length=1, choices=ActionType.choices)
    timestamp_ts = models.DateTimeField(auto_now_add=True, blank=True)

    @property
    def message(self):
        if self.action_type == self.ActionType.CHOOSE_GIFT:
            return '{:%H:%M:%S}: {} unwrapped a {}'.format(
                self.timestamp_ts,
                self.by_user_id,
                self.gift_id.description,
            )
        elif self.action_type == self.ActionType.TRANSFERRED:
            return '{:%H:%m:%s}: {} transferred {} from {} to {}'.format(
                self.timestamp_ts,
                self.by_user_id,
                self.gift_id.description,
                self.from_user_id,
                self.to_user_id
            )
