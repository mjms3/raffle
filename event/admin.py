from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from event.models import Gift, RaffleEvent, RaffleParticipation, Action


class RaffleEventAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phase',
        'raffle_actions',
    )

    def raffle_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Change picker</a>&nbsp;'
            '<a class="button" href="{}">Permute Images</a>&nbsp;'
            '<a class="button" href="{}">Reset</a>',
            reverse('change_picker', args=[obj.pk]),
            reverse('permute_images', args=[obj.pk]),
            reverse('reset_raffle', args=[obj.pk]),
        )
    raffle_actions.short_description = 'Raffle Actions'
    raffle_actions.allow_tags = True

class GiftAdmin(admin.ModelAdmin):
    list_display = (
        'description',
        'added_by',
        'wrapped'
    )

class RaffleParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'user',
        'number_of_tickets',
        'number_of_times_drawn',
    )

admin.site.register(Gift,GiftAdmin)
admin.site.register(RaffleEvent, RaffleEventAdmin)
admin.site.register(RaffleParticipation, RaffleParticipationAdmin)
admin.site.register(Action)
