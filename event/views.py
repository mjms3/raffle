from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView

from event.models import Action
from gifts.models import Gift


class EventView(ListView):
    template_name = 'event.html'
    model = Gift


@login_required
def unwrap_image(request):
    gift_id = int(request.POST['image_id'].replace('image-', ''))
    gift = get_object_or_404(Gift, id=gift_id)
    data = {
        'image': gift.image.url,
        'element': '#{}'.format(request.POST['image_id'])
    }
    gift.given_to = request.user
    gift.wrapped = False
    event = Action(gift_id=gift,
                   from_user_id=gift.added_by,
                   to_user_id=request.user,
                   by_user_id=request.user,
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
