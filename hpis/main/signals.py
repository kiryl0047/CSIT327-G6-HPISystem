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
            # Determine default role for the newly created user
            if instance.is_superuser:
                default_role = 'super_admin'
            elif instance.is_staff:
                default_role = 'admin'
            else:
                default_role = 'doctor'

            # Create a basic profile; fields must match the UserProfile model
            UserProfile.objects.create(
                user=instance,
                role=default_role,
                department='',
                license_number=''
            )
            print(f"✓ UserProfile created for {instance.username} with role {default_role}")
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
            NotificationPreference.objects.get_or_create(
                user=instance,
                defaults={
                    'email_notifications': True,
                    'sms_notifications': True,
                    'prescription_alerts': True,
                    'system_updates': True,
                }
            )
            print(f"✓ NotificationPreference ensured for {instance.username}")
        except Exception as e:
            print(f"✗ Error ensuring NotificationPreference: {e}")