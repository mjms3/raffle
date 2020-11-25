from django.urls import path

from event import views

urlpatterns = [
    path('<int:event_id>/',  views.EventView.as_view(), name='event_index'),
    path('gifts/', views.GiftIndexView.as_view(), name='gift_index'),
    path('gifts/update/<pk>/', views.GiftUpdateView.as_view(), name='update_gift'),
    path('gifts/delete/<pk>/', views.GiftDeleteView.as_view(), name='delete_gift'),
    path('gifts/donate/', views.GiftCreateView.as_view(), name='gift_create'),
    path('gifts/donations/', views.MyGiftsView.as_view(), name='my_donations'),
    path('tickets/', views.MyTicketsView.as_view(), name='my_tickets'),
    path('tickets/create/', views.RaffleParticipationCreateView.as_view(), name='create_participation'),
    path('tickets/update/<pk>/', views.RaffleParticipationUpdateView.as_view(), name='update_participation'),
    path('tickets/delete/<pk>/', views.RaffleParticipationDeleteView.as_view(), name='delete_participation'),
    path('api/process_image_click/', views.process_image_click, name='process_image_click'),
    path('api/process_swap_gift/', views.process_swap_gift, name='process_swap_gift'),
    path('api/stream/', views.stream, name='event_stream'),
    path('api/change_picker/<int:event_id>', views.change_current_gift_picker, name='change_picker'),
    path('api/rotate_image/<int:gift_id>/<int:angle>', views.rotate_image, name='rotate_image'),
]
