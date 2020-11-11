from django.urls import path

from django.contrib.auth.urls import urlpatterns as auth_urlpatterns

from account import views

urlpatterns = auth_urlpatterns + [
    path('signup/', views.NewUserView.as_view(), name='signup'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('password/', views.change_password, name='change_password')
]
