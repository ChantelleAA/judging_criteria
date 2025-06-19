from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from judging.models import Judge

class Command(BaseCommand):
    help = 'Send login credentials to all judges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--judge-email',
            type=str,
            help='Send credentials to specific judge by email',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        # Get portal URL (you might want to make this configurable)
        portal_url = getattr(settings, 'JUDGING_PORTAL_URL', 'http://127.0.0.1:8000/')
        
        # Determine which judges to send credentials to
        if options['judge_email']:
            try:
                judge = Judge.objects.get(user__email=options['judge_email'])
                judges = [judge]
                self.stdout.write(f"Sending credentials to: {judge.user.get_full_name()}")
            except Judge.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Judge with email {options['judge_email']} not found")
                )
                return
        else:
            judges = Judge.objects.all()
            self.stdout.write(f"Sending credentials to {judges.count()} judges")

        sent_count = 0
        for judge in judges:
            try:
                # Prepare context for email template
                expertise_areas = ', '.join([area.name for area in judge.expertise_areas.all()])
                context = {
                    'judge': judge,
                    'expertise_areas': expertise_areas,
                    'portal_url': portal_url,
                }

                # Render email templates
                html_message = render_to_string('judging/email/judge_credentials.html', context)
                plain_message = render_to_string('judging/email/judge_credentials.txt', context)

                if options['dry_run']:
                    self.stdout.write(f"Would send email to: {judge.user.email}")
                    self.stdout.write(f"Subject: Hackathon Judge Login Credentials - Welcome!")
                    self.stdout.write("="*50)
                    continue

                # Send email
                send_mail(
                    subject='Hackathon Judge Login Credentials - Welcome!',
                    message=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hackathon.com'),
                    recipient_list=[judge.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Sent credentials to {judge.user.get_full_name()} ({judge.user.email})")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to send to {judge.user.get_full_name()}: {str(e)}")
                )

        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully sent credentials to {sent_count} judges!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"\nDry run complete. Would have sent {len(judges)} emails.")
            )

# Add to settings.py for email configuration
"""
# Email Configuration (add to settings.py)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Hackathon Judging <noreply@hackathon.com>'

# For development, you can use console backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Portal URL
JUDGING_PORTAL_URL = 'https://your-domain.com/'  # Update with your actual domain
"""