from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from event.models import Action, Gift, RaffleEvent


class EventView(LoginRequiredMixin, ListView):
    template_name = 'event.html'
    model = Gift

    def get_queryset(self):
        event = get_object_or_404(RaffleEvent, id=self.kwargs['event_id'])
        return Gift.objects.filter(event=event)

class GiftIndexView(PermissionRequiredMixin, ListView):
    permission_required = 'gifts.view_gift'
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


@login_required
def process_image_click(request):
    event = get_object_or_404(RaffleEvent, id = request.POST['event_id'] )
    if event.phase in (event.Phase.PRE_START, event.Phase.FINISHED):
        return JsonResponse({'error': 'Raffle not in progress'})
    gift_id = int(request.POST['image_id'].replace('image-', ''))
    gift = get_object_or_404(Gift, id=gift_id)

    assert gift.event is event, 'Gift: %s and event: %s are inconsistent' %(gift, event)

    data = {
        'image': gift.image.url,
        'element': '#{}'.format(request.POST['image_id'])
    }
    gift.given_to = request.user
    gift.wrapped = False
    event = Action(gift=gift,
                   from_user=gift.added_by,
                   to_user=request.user,
                   by_user=request.user,
                   action_type=Action.ActionType.CHOOSE_GIFT,
                   )
    gift.save()
    event.save()
    return JsonResponse(data)


@login_required
def stream(request):
    last_processed_event= request.POST.get('last_processed_event',0)
    activity = Action.objects.filter(id__gt=last_processed_event)
    return JsonResponse({
        'activity': [a.message for a in activity],
        'last_event': max(a.id for a in activity) if len(activity)>0 else last_processed_event,
    })
