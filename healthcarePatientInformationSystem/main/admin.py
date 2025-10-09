from django.contrib import admin
from .models import (
    UserProfile, NotificationPreference, AccessLog,
    DataExportRequest, DeleteAccountRequest
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'profession', 'created_at', 'updated_at')
    list_filter = ('user_type', 'profession', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Details', {
            'fields': ('user_type', 'profession')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_notifications',
                    'prescription_alerts', 'system_updates', 'updated_at')
    list_filter = ('email_notifications', 'sms_notifications',
                   'prescription_alerts', 'system_updates')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications',
                       'prescription_alerts', 'system_updates')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_type', 'ip_address', 'timestamp')
    list_filter = ('access_type', 'timestamp', 'user')
    search_fields = ('user__username', 'user__email', 'ip_address', 'description')
    readonly_fields = ('user', 'access_type', 'ip_address', 'user_agent',
                       'description', 'timestamp')
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('User & Access Info', {
            'fields': ('user', 'access_type', 'timestamp')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'completed_at', 'expires_at')
    list_filter = ('status', 'requested_at', 'completed_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'requested_at', 'completed_at', 'download_url')
    date_hierarchy = 'requested_at'

    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'status', 'requested_at')
        }),
        ('Completion Details', {
            'fields': ('completed_at', 'expires_at', 'download_url'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeleteAccountRequest)
class DeleteAccountRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'confirmed_at', 'scheduled_deletion_date')
    list_filter = ('status', 'requested_at', 'confirmed_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'requested_at', 'confirmed_at', 'deleted_at')
    date_hierarchy = 'requested_at'

    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'status', 'requested_at')
        }),
        ('Confirmation & Deletion', {
            'fields': ('confirmed_at', 'deleted_at', 'scheduled_deletion_date'),
            'classes': ('collapse',)
        }),
        ('Reason for Deletion', {
            'fields': ('reason',)
        }),
    )

    actions = ['mark_as_deleted']

    def mark_as_deleted(self, request, queryset):
        """Admin action to mark accounts as deleted"""
        from django.utils import timezone
        updated = queryset.filter(status='confirmed').update(
            status='deleted',
            deleted_at=timezone.now()
        )
        self.message_user(request, f'{updated} account(s) marked as deleted.')

    mark_as_deleted.short_description = "Mark selected as deleted"