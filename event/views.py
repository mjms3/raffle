from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView

from gifts.models import Gift


class EventView(ListView):
    template_name = 'event.html'
    model = Gift


def unwrap_image(request):
    gift_id = int(request.POST['image_id'].replace('image-', ''))
    gift = get_object_or_404(Gift, id=gift_id)
    data = {
        'image': gift.image.url,
        'element': '#{}'.format(request.POST['image_id'])
    }
    return JsonResponse(data)
