from django.contrib import admin

from event.models import Gift, RaffleEvent, RaffleParticipation

admin.site.register(Gift)
admin.site.register(RaffleEvent)
admin.site.register(RaffleParticipation)