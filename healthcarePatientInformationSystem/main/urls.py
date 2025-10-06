from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("", views.user_login, name="user_login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", LogoutView.as_view(next_page="user_login"), name="logout"),
    path("homepage/", views.homepage, name="homepage"),
    path("book_appointment/", views.book_appointment, name="book_appointment"),
    path("upcoming_appointments/", views.upcoming_appointments, name="upcoming_appointments"),
    path("request_prescription/", views.request_prescription, name="request_prescription"),
]

