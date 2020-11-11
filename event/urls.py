from django.urls import path

from event import views

urlpatterns = [
    path('',  views.EventView.as_view(), name='index'),
    path('api/process_image_click/', views.process_image_click, name='process_image_click'),
    path('api/stream/', views.stream, name='event_stream'),
]
