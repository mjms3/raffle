
from django import template

from event.models import RaffleEvent

register = template.Library()

@register.simple_tag
def get_all_events():
    return RaffleEvent.objects.all()