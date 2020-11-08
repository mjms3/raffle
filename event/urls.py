from django.urls import path

from event.views import EventView

urlpatterns = [
    path('', EventView.as_view(), name='index'),
]
