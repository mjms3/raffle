from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import F
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from event.models import Action, Gift, RaffleEvent, RaffleParticipation
import random


class EventView(LoginRequiredMixin, ListView):
    template_name = 'event.html'
    model = Gift

    def get_queryset(self):
        event = get_object_or_404(RaffleEvent, id=self.kwargs['event_id'])
        return Gift.objects.filter(event=event)


class GiftIndexView(PermissionRequiredMixin, ListView):
    permission_required = 'view_gift'
    template_name = 'gift_index.html'
    model = Gift


class MyGiftsView(LoginRequiredMixin, ListView):
    template_name = 'gift_index.html'
    model = Gift

    def get_queryset(self):
        return Gift.objects.filter(added_by=self.request.user)


class GiftCreateView(LoginRequiredMixin, CreateView):
    model = Gift
    fields = ['description', 'image', 'event']
    template_name = 'gift_form.html'
    success_url = reverse_lazy('my_donations')

    def form_valid(self, form):
        gift = form.save(commit=False)
        gift.added_by = self.request.user
        gift.save()
        self.object = gift
        return HttpResponseRedirect(self.get_success_url())


@permission_required('change_raffleevent')
def change_current_gift_picker(request, event_id):
    raffle_event = get_object_or_404(RaffleEvent, id=event_id)
    assert raffle_event.phase == RaffleEvent.Phase.NORMAL_RAFFLE
    raffle_participants = RaffleParticipation.objects.filter(event_id=raffle_event.id).filter(
        number_of_tickets__gt=F('number_of_times_drawn'))
    weights = [r.number_of_tickets - r.number_of_times_drawn for r in raffle_participants]
    next_person = random.choices(raffle_participants, weights)
    assert len(next_person)==1, next_person
    next_person = next_person[0]
    action = Action(
        event=raffle_event,
        gift=None,
        from_user=None,
        to_user=next_person.user,
        by_user=request.user,
        action_type=Action.ActionType.CHANGED_USER
    )
    next_person.number_of_times_drawn += 1
    raffle_event.current_user = next_person.user
    raffle_event.save()
    action.save()
    next_person.save()
    return JsonResponse({'success':True})
    

@login_required
def process_image_click(request):
    raffle_event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])
    if raffle_event.phase in (raffle_event.Phase.PRE_START, raffle_event.Phase.FINISHED):
        return JsonResponse({'error': 'Raffle not in progress'})
    gift_id = int(request.POST['image_id'].replace('image-', ''))
    gift = get_object_or_404(Gift, id=gift_id)

    assert gift.event == raffle_event, 'Gift: %s and RaffleEvent: %s are inconsistent' % (gift, raffle_event)
    if not gift.wrapped:
        return JsonResponse({'error':'Gift already unwrapped'})
    data = {
        'image': gift.image.url,
        'element': '#{}'.format(request.POST['image_id'])
    }
    gift.given_to = request.user
    gift.wrapped = False
    action = Action(gift=gift,
                    from_user=gift.added_by,
                    to_user=request.user,
                    by_user=request.user,
                    action_type=Action.ActionType.CHOOSE_GIFT,
                    event=raffle_event,
                    )
    gift.save()
    action.save()
    return JsonResponse(data)


@login_required
def stream(request):
    event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])

    last_processed_action = request.POST.get('last_processed_action', 0)
    activity = Action.objects.filter(id__gt=last_processed_action,
                                     event=event,
                                     )
    return JsonResponse({
        'activity': [a.message for a in activity],
        'last_event': max(a.id for a in activity) if len(activity) > 0 else last_processed_action,
    })
