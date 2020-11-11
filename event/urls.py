from django.urls import path

from event import views

urlpatterns = [
    path('<int:event_id>/',  views.EventView.as_view(), name='index'),
    path('gifts/', views.GiftIndexView.as_view(), name='index'),
    path('gifts/donate', views.GiftCreateView.as_view(), name='gift_create'),
    path('gifts/donations', views.MyGiftsView.as_view(), name='my_donations'),
    path('api/process_image_click/', views.process_image_click, name='process_image_click'),
    path('api/stream/', views.stream, name='event_stream'),
    path('api/change_picker/<int:event_id>', views.change_current_gift_picker, name='change_picker')
]
