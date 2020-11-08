from django.urls import path

from event import views

urlpatterns = [
    path('',  views.EventView.as_view(), name='index'),
    path('api/unwrap_image/', views.unwrap_image, name='unwrap_image'),
path('api/stream/', views.stream, name='unwrap_image'),
]
