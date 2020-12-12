from io import BytesIO
from operator import itemgetter
from random import shuffle

from PIL import Image
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db import transaction
from django.db.models import ForeignObjectRel
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from account.models import CustomUser
from event.models import Action, Gift, RaffleEvent, _pick_next_person, RaffleParticipation
from event.serializers import RaffleEventSerializer


class EventView(LoginRequiredMixin, ListView):
    template_name = 'event.html'
    model = Gift

    def get_queryset(self):
        event = get_object_or_404(RaffleEvent, id=self.kwargs['event_id'])
        return Gift.objects.filter(event=event)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        event = get_object_or_404(RaffleEvent, id=self.kwargs['event_id'])
        context['user_mapping'] = sorted(((u.id, u.display_name) for u in event.participants.all()), key=itemgetter(1))
        return context

class GiftIndexView(PermissionRequiredMixin, ListView):
    permission_required = 'view_gift'
    template_name = 'gift_index.html'
    model = Gift

    def get_queryset(self):
        return super().get_queryset().order_by('add_ts')


class MyGiftsView(LoginRequiredMixin, ListView):
    template_name = 'gift_index.html'
    model = Gift

    def get_queryset(self):
        return Gift.objects.filter(added_by=self.request.user).order_by('add_ts')

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
    return JsonResponse({'success': True})

@permission_required('change_raffleevent')
def permute_images(request, event_id):
    raffle_event = get_object_or_404(RaffleEvent, id=event_id)

    with transaction.atomic():
        gifts = Gift.objects.filter(event_id=raffle_event.id)
        container_ids = [r.id for r in gifts]
        shuffle(container_ids)
        for gift, container_id in zip(gifts, container_ids):
            gift.container_id = container_id
        Gift.objects.bulk_update(gifts, ['container_id'])
    return JsonResponse({'success': True})

@permission_required('change_raffleevent')
def reset_raffle(request, event_id):
    raffle_event = get_object_or_404(RaffleEvent, id=event_id)

    with transaction.atomic():
        raffle_event.phase = RaffleEvent.Phase.PRE_START
        raffle_event.current_user = None
        raffle_event.save()

        gifts = raffle_event.gift_set
        gifts.update(wrapped=True, container_id=None, given_to=None)

        participantions = raffle_event.raffleparticipation_set
        participantions.update(number_of_times_drawn=0)

        actions = raffle_event.action_set.all()
        actions.delete()

    return JsonResponse({'success': True})


@permission_required('change_raffleevent')
@api_view(('GET',))
@renderer_classes((JSONRenderer,))
def summarise_raffle(request,event_id):
    raffle_event = get_object_or_404(RaffleEvent, id=event_id)
    serializer = RaffleEventSerializer(raffle_event)
    return Response(serializer.data)

@login_required
def rotate_image(request, gift_id, angle):
    current_user = request.user
    gift = get_object_or_404(Gift, id=gift_id)
    if gift.added_by != current_user:
        if current_user.is_superuser is False:
            return HttpResponseForbidden()
    if angle not in (90, 180, 270):
        return HttpResponseBadRequest()
    image_stream = BytesIO()
    pixelated_image_stream = BytesIO()

    img = Image.open(BytesIO(gift.image.read()))
    img.rotate(angle, expand=1).save(image_stream, format=img.format)

    pixelated_image = Image.open(BytesIO(gift.pixelated_image.read()))
    pixelated_image.rotate(angle, expand=1).save(pixelated_image_stream, format=pixelated_image.format)

    gift.save(new_image_data=(image_stream, pixelated_image_stream))

    return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse_lazy('my_donations'))


@login_required
def process_image_click(request):
    raffle_event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])
    if raffle_event.phase in (raffle_event.Phase.PRE_START, raffle_event.Phase.FINISHED):
        return JsonResponse({'error': 'Raffle not in progress'})

    gift_id = int(request.POST['image_id'].replace('image-', ''))
    gift = get_object_or_404(Gift, id=gift_id)

    if raffle_event.phase == raffle_event.Phase.NORMAL_RAFFLE:
        if raffle_event.current_user != request.user:
            return JsonResponse({'error': "It's not your turn to pick a gift!"})
        if raffle_event.gift_set.filter(wrapped=True).count() == 0:
            return JsonResponse({'error': "All gifts have been unwrapped."})

        if gift.event != raffle_event:
            return JsonResponse({'error': 'Gift: %s and RaffleEvent: %s are inconsistent' % (gift, raffle_event)})
        if not gift.wrapped:
            return JsonResponse({'error': 'Gift already unwrapped'})

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
        return JsonResponse({
            'error': None,
            'gift_description': gift.description,
            'gift_image_url': gift.image_url,
            'gift_id':gift.id,
        })
    elif raffle_event.phase == raffle_event.Phase.GIFT_SWAP:
        return JsonResponse({'modal_data': {
            'gift_id': gift.id,
            'gift_description': gift.description,
            'current_user_display_name': gift.given_to.display_name,
            'current_user_id': gift.given_to_id,
        }})


@login_required
def process_swap_gift(request):
    raffle_event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])
    if raffle_event.phase != RaffleEvent.Phase.GIFT_SWAP:
        return JsonResponse({'error': 'Gift swap not in progress'})

    with transaction.atomic():
        gift = get_object_or_404(Gift, id=request.POST['gift_id'])
        if gift.given_to_id != int(request.POST['current_user_id']):
            return JsonResponse(
                {'error': 'Looks like someone else has already swapped the owner of %s' % gift.description})
        swap_to = get_object_or_404(CustomUser, id=request.POST['to_user_id'])
        action = Action(gift=gift,
                        from_user=gift.given_to,
                        to_user=swap_to,
                        by_user=request.user,
                        action_type=Action.ActionType.TRANSFERRED,
                        event=raffle_event,
                        )
        gift.given_to = swap_to
        action.save()
        gift.save()
    return JsonResponse({'error':None})

@login_required
def stream(request):
    event = get_object_or_404(RaffleEvent, id=request.POST['event_id'])

    last_processed_action = request.POST.get('last_processed_action', 0)
    activity = Action.objects.filter(id__gt=last_processed_action,
                                     event=event,
                                     )
    container_contents = {r.image_container_id:
        {
            'src_url': r.image_url,
            'gift_id': r.id,
            'unwrapped': not r.wrapped,
            'given_to': r.given_to.display_name if r.given_to else None,
            'gift_description': '' if r.wrapped else r.description,
        } for r in event.gift_set.all()}

    user_status_text = _get_user_status_text(event, request)

    return JsonResponse({
        'activity': [a.message for a in activity],
        'last_event': max(a.id for a in activity) if len(activity) > 0 else last_processed_action,
        'container_contents': container_contents,
        'user_status': user_status_text,
    })


def _get_user_status_text(event, request):
    user_status_template = '{user}: {tickets}{swaps} {cost}'
    ticket_details = request.user.raffleparticipation_set.filter(event_id=event.id).first()
    total_owed = 0
    if not ticket_details:
        tickets_text = 'No tickets for the raffle'
    else:
        tickets_text = '{} tickets of {} drawn'.format(
            ticket_details.number_of_times_drawn,
            ticket_details.number_of_tickets,
        )
        total_owed += 5 * ticket_details.number_of_tickets
    if event.phase in (RaffleEvent.Phase.GIFT_SWAP, RaffleEvent.Phase.FINISHED):
        swaps = request.user.initiated_actions.filter(
            action_type=Action.ActionType.TRANSFERRED,
            event=event.id).count()
        swaps_text = ', swapped {} gifts'.format(swaps)
        total_owed += 5 * swaps
    else:
        swaps_text = ''
    user_status_text = user_status_template.format(
        user=request.user,
        tickets=tickets_text,
        swaps=swaps_text,
        cost='(&pound;{} owed)'.format(total_owed),
    )
    return user_status_text
