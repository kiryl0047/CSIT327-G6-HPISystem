from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from main.models import DeleteAccountRequest, DataExportRequest, AccessLog
from datetime import timedelta


class Command(BaseCommand):
    help = 'Perform HPIS cleanup tasks: delete accounts, clean old logs, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-accounts',
            action='store_true',
            help='Delete accounts that have passed their scheduled deletion date'
        )
        parser.add_argument(
            '--clean-logs',
            action='store_true',
            help='Delete old access logs (older than 90 days)'
        )
        parser.add_argument(
            '--clean-exports',
            action='store_true',
            help='Delete expired data exports'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting HPIS cleanup tasks...'))

        if options['delete_accounts'] or not any([options['delete_accounts'],
                                                  options['clean_logs'],
                                                  options['clean_exports']]):
            self.delete_scheduled_accounts()

        if options['clean_logs'] or not any([options['delete_accounts'],
                                             options['clean_logs'],
                                             options['clean_exports']]):
            self.clean_old_logs()

        if options['clean_exports'] or not any([options['delete_accounts'],
                                                options['clean_logs'],
                                                options['clean_exports']]):
            self.clean_expired_exports()

        self.stdout.write(self.style.SUCCESS('Cleanup tasks completed!'))

    def delete_scheduled_accounts(self):
        """Delete accounts that have passed their scheduled deletion date"""
        now = timezone.now()

        # Get accounts ready for deletion
        deletion_requests = DeleteAccountRequest.objects.filter(
            status='confirmed',
            scheduled_deletion_date__lte=now
        )

        deleted_count = 0
        for request in deletion_requests:
            try:
                user = request.user
                username = user.username

                # Delete user and associated data
                user.delete()

                # Update request status
                request.status = 'deleted'
                request.deleted_at = now
                request.save()

                deleted_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted user account: {username}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error deleting user: {str(e)}')
                )

        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} account(s)')
            )
        else:
            self.stdout.write('No accounts scheduled for deletion at this time.')

    def clean_old_logs(self):
        """Delete access logs older than 90 days"""
        cutoff_date = timezone.now() - timedelta(days=90)

        old_logs = AccessLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()

        old_logs.delete()

        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} old access log(s)')
            )
        else:
            self.stdout.write('No old access logs to delete.')

    def clean_expired_exports(self):
        """Delete expired data export requests and associated files"""
        now = timezone.now()

        expired_exports = DataExportRequest.objects.filter(
            status='completed',
            expires_at__lte=now
        )

        count = expired_exports.count()
        expired_exports.delete()

        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} expired data export(s)')
            )
        else:
            self.stdout.write('No expired data exports to delete.')