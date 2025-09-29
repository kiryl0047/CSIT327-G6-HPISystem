from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("", views.user_login, name='user_login'),
    path("signup/", views.signup, name='signup'),
    path("password_reset/", views.password_reset, name='password_reset'),
    path("logout/", LogoutView.as_view(next_page="user_login"), name="logout"),
]