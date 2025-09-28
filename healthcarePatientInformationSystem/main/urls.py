from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name='index'),
    path("login/", views.user_login, name='user_login'),
    path("signup/", views.signup, name='signup'),
    path("password_reset/", views.password_reset, name='password_reset'),
]