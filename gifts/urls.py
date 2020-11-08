from django.urls import path

from gifts.views import IndexView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
