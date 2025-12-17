from django.core.management.base import BaseCommand
from django.conf import settings
import socket
import smtplib
import ssl


class Command(BaseCommand):
    help = 'Check SMTP connectivity and (optionally) attempt login / send a test email.'

    def add_arguments(self, parser):
        parser.add_argument('--send-test', action='store_true', help='Send a small test email (requires EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)')
        parser.add_argument('--recipient', type=str, help='Recipient email for test send (required with --send-test)')

    def handle(self, *args, **options):
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        port = int(getattr(settings, 'EMAIL_PORT', 587))
        user = getattr(settings, 'EMAIL_HOST_USER', None)
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)

        self.stdout.write(self.style.MIGRATE_HEADING(f'Checking SMTP connectivity to {host}:{port}'))

        # TCP connect test
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                self.stdout.write(self.style.SUCCESS(f'TCP connection to {host}:{port} OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'FAILED to connect to {host}:{port}: {e}'))
            raise SystemExit(1)

        # SMTP handshake + STARTTLS
        try:
            server = smtplib.SMTP(host=host, port=port, timeout=10)
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            self.stdout.write(self.style.SUCCESS('SMTP STARTTLS handshake succeeded'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'SMTP handshake/starttls failed: {e}'))
            raise SystemExit(2)

        # If credentials are present, try login (do not send mail unless asked)
        if user and password:
            try:
                server.login(user, password)
                self.stdout.write(self.style.SUCCESS('SMTP login succeeded'))
            except smtplib.SMTPAuthenticationError as e:
                self.stdout.write(self.style.ERROR(f'SMTP authentication failed: {e}'))
                raise SystemExit(3)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'SMTP login failed: {e}'))
                raise SystemExit(4)
        else:
            self.stdout.write(self.style.WARNING('EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set — skipping login test'))

        # Optionally send a test email
        if options.get('send_test'):
            recipient = options.get('recipient')
            if not recipient:
                self.stdout.write(self.style.ERROR('--recipient is required when using --send-test'))
                raise SystemExit(5)
            try:
                subject = 'Pinmate SMTP test'
                body = 'This is a test email from Pinmate SMTP check.'
                msg = f'Subject: {subject}\n\n{body}'
                server.sendmail(user, [recipient], msg)
                self.stdout.write(self.style.SUCCESS(f'Test email sent to {recipient}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to send test email: {e}'))
                raise SystemExit(6)

        server.quit()

        self.stdout.write(self.style.SUCCESS('SMTP check completed successfully'))
