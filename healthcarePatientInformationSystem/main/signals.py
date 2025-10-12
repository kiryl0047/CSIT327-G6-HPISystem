from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, NotificationPreference


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile when a new User is created.
    This signal fires after a User is saved to the database.
    """
    if created:
        try:
            UserProfile.objects.create(
                user=instance,
                user_type='patient',
                profession='patient'
            )
            print(f"✓ UserProfile created for {instance.username}")
        except Exception as e:
            print(f"✗ Error creating UserProfile: {e}")


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """
    Automatically create NotificationPreference when a new User is created.
    This signal fires after a User is saved to the database.
    """
    if created:
        try:
            NotificationPreference.objects.create(
                user=instance,
                email_notifications=True,
                sms_notifications=True,
                prescription_alerts=True,
                system_updates=True
            )
            print(f"✓ NotificationPreference created for {instance.username}")
        except Exception as e:
            print(f"✗ Error creating NotificationPreference: {e}")