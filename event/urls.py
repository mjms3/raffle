from django.urls import path

from event import views

urlpatterns = [
    path('',  views.EventView.as_view(), name='index'),
    path('ajax/unwrap_image/', views.unwrap_image, name='unwrap_image')
]
