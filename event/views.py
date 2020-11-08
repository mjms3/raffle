from django.shortcuts import render
from django.views.generic import ListView

from gifts.models import Gift


class EventView(ListView):
    template_name = 'event.html'
    model = Gift