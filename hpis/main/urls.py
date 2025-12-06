from django.urls import include, path
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
    path('records/', include('records.urls')),

    # Doctor URLs
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("doctor/confirm-appointment/<int:appointment_id>/", views.confirm_appointment, name="confirm_appointment"),

    # Profile & Settings URLs
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    path("settings/update-profile", views.update_profile, name="update_profile"),
    path("settings/change-password/", views.change_password, name="change_password"),
    path("settings/update-notifications/", views.update_notifications, name="update_notifications"),
    path("settings/download-user-data", views.download_user_data, name="download_user_data"),
    path("settings/request-data-export", views.request_data_export, name="request_data_export"),
    path("settings/request-account-deletion", views.request_account_deletion, name="request_account_deletion"),
    path('records/', include('records.urls')),

    # Analytics & Reports URLs
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("analytics/reports/", views.generate_report, name="reports"),
    path("homepage/", views.analytics_dashboard, name="dashboard_url"),
]