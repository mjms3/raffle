from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from event.models import Action, Gift, RaffleEvent, _pick_next_person, RaffleParticipation


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

class GiftUpdateView(LoginRequiredMixin, UpdateView):
    model = Gift
    fields = ['description', 'image', 'event']
    template_name = 'gift_form.html'
    success_url = reverse_lazy('my_donations')

    def get_queryset(self):
        base_qs = super(GiftUpdateView, self).get_queryset()
        return base_qs.filter(added_by=self.request.user)

class GiftDeleteView(LoginRequiredMixin, DeleteView):
    model = Gift
    success_url = reverse_lazy('my_donations')
    template_name = 'gift_delete_confirmation.html'

    def get_queryset(self):
        base_qs = super(GiftDeleteView, self).get_queryset()
        return base_qs.filter(added_by=self.request.user)

class MyTicketsView(LoginRequiredMixin, ListView):
    template_name = 'ticket_index.html'
    model = RaffleParticipation

    def get_queryset(self):
        return RaffleParticipation.objects.filter(user=self.request.user)

class RaffleParticipationCreateView(LoginRequiredMixin, CreateView):
    model = RaffleParticipation
    fields = ['event','number_of_tickets']
    template_name = 'ticket_form.html'
    success_url = reverse_lazy('my_tickets')

    def form_valid(self, form):
        raffle_participation = form.save(commit=False)
        raffle_participation.user = self.request.user
        raffle_participation.save()
        self.object = raffle_participation
        return HttpResponseRedirect(self.get_success_url())

class RaffleParticipationUpdateView(LoginRequiredMixin, UpdateView):
    model = RaffleParticipation
    fields = ['number_of_tickets']
    template_name = 'ticket_form.html'
    success_url = reverse_lazy('my_tickets')

    def get_queryset(self):
        base_qs = super(RaffleParticipationUpdateView, self).get_queryset()
        return base_qs.filter(user=self.request.user)

class RaffleParticipationDeleteView(LoginRequiredMixin, DeleteView):
    model = RaffleParticipation
    success_url = reverse_lazy('my_tickets')
    template_name = 'raffle_participation_delete_confirmation.html'

    def get_queryset(self):
        base_qs = super(RaffleParticipationDeleteView, self).get_queryset()
        return base_qs.filter(user=self.request.user)

@permission_required('change_raffleevent')
def change_current_gift_picker(request, event_id):
    raffle_event = get_object_or_404(RaffleEvent, id=event_id)
    current_user = request.user
    with transaction.atomic():
        _pick_next_person(current_user, raffle_event)
    return JsonResponse({'success':True})


@login_required
def process_image_click(request):
    raffle_event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])
    if raffle_event.phase in (raffle_event.Phase.PRE_START, raffle_event.Phase.FINISHED):
        return JsonResponse({'error': 'Raffle not in progress'})
    if raffle_event.current_user != request.user:
        return JsonResponse({'error': "It's not your turn to pick a gift!"})

    gift_id = int(request.POST['image_id'].replace('image-', ''))
    gift = get_object_or_404(Gift, id=gift_id)
    if gift.event != raffle_event:
        return JsonResponse({'error':'Gift: %s and RaffleEvent: %s are inconsistent' % (gift, raffle_event)})
    if not gift.wrapped:
        return JsonResponse({'error':'Gift already unwrapped'})

    gift.given_to = request.user
    gift.wrapped = False
    action = Action(gift=gift,
                    from_user=gift.added_by,
                    to_user=request.user,
                    by_user=request.user,
                    action_type=Action.ActionType.CHOOSE_GIFT,
                    event=raffle_event,
                    )
    with transaction.atomic():
        gift.save()
        action.save()
        _pick_next_person(current_user=request.user, raffle_event=raffle_event)
    return JsonResponse({'error':None})


@login_required
def stream(request):
    event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])

    last_processed_action = request.POST.get('last_processed_action', 0)
    activity = Action.objects.filter(id__gt=last_processed_action,
                                     event=event,
                                     )
    image_urls = {r.image_id:r.image_url for r in Gift.objects.filter(event_id=event.id)}
    return JsonResponse({
        'activity': [a.message for a in activity],
        'last_event': max(a.id for a in activity) if len(activity) > 0 else last_processed_action,
        'image_urls': image_urls,
    })
