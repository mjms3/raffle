from django.contrib import admin
from django.db.models import F
from django.urls import reverse
from django.utils.html import format_html

from event.models import Gift, RaffleEvent, RaffleParticipation, Action


class RaffleEventAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phase',
        'current_user',
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
        'wrapped',
        'id',
        'container_id',
        'given_to',
    )

class RaffleParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'user',
        'number_of_tickets',
        'number_of_times_drawn',
    )

    actions = ["remove_from_raffle"]

    def remove_from_raffle(self, request, queryset):
        queryset.update(number_of_times_drawn=F('number_of_tickets'))
    remove_from_raffle.short_description = 'Remove from raffle'

admin.site.register(Gift,GiftAdmin)
admin.site.register(RaffleEvent, RaffleEventAdmin)
admin.site.register(RaffleParticipation, RaffleParticipationAdmin)
admin.site.register(Action)
