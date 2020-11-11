from django.urls import path

from django.contrib.auth.urls import urlpatterns as auth_urlpatterns

from account import views

urlpatterns = auth_urlpatterns + [
    path('signup/', views.NewUserView.as_view(), name='signup'),
]
