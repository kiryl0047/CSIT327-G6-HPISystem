from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Authentication
    path("", views.landing_page, name="landing_page"),
    path("login/", views.user_login, name="user_login"),
    path("logout/", LogoutView.as_view(next_page="landing_page"), name="logout"),
    path("homepage/", views.homepage, name="homepage"),

    # Super Admin URLs
    path("admin/dashboard/", views.super_admin_dashboard, name="super_admin_dashboard"),
    path("admin/create-staff/", views.create_staff, name="create_staff"),
    path("admin/manage-staff/", views.manage_staff, name="manage_staff"),
    path("admin/edit-staff/<int:staff_id>/", views.edit_staff, name="edit_staff"),
    path("admin/delete-staff/<int:staff_id>/", views.delete_staff, name="delete_staff"),

    # Admin URLs
    path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/assign-appointment/<int:appointment_id>/", views.assign_appointment, name="assign_appointment"),

    # Doctor URLs
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("doctor/confirm-appointment/<int:appointment_id>/", views.confirm_appointment, name="confirm_appointment"),

    # Settings URLs
    path("settings/", views.settings_page, name="settings"),
    path("settings/change-password/", views.change_password, name="change_password"),
    path("settings/update-notifications/", views.update_notifications, name="update_notifications"),
]