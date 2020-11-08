from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, ListView

from gifts.models import Gift


class IndexView(ListView):
    template_name = 'index.html'
    model = Gift