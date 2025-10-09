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

    # New Settings URLs
    path("settings/", views.settings_page, name="settings"),
    path("settings/update-profile/", views.update_profile, name="update_profile"),
    path("settings/change-password/", views.change_password, name="change_password"),
    path("settings/update-notifications/", views.update_notifications, name="update_notifications"),
    path("settings/access-logs/", views.access_logs, name="access_logs"),
    path("settings/request-data-export/", views.request_data_export, name="request_data_export"),
    path("settings/download-user-data/", views.download_user_data, name="download_user_data"),
    path("settings/request-deletion/", views.request_account_deletion, name="request_account_deletion"),
    path("settings/confirm-deletion/", views.confirm_account_deletion, name="confirm_account_deletion"),
    path("settings/cancel-deletion/", views.cancel_account_deletion, name="cancel_account_deletion"),
]

