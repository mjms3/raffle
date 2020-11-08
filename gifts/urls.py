from django.urls import path

from gifts.views import IndexView, GiftCreateView, MyGiftsView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('donate', GiftCreateView.as_view(), name='gift_create'),
    path('donations', MyGiftsView.as_view(), name='my_donations')
]
