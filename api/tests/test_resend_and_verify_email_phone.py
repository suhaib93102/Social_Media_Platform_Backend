from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse
from datetime import timedelta
from unittest.mock import patch

from api.models import PendingSignup, OTPVerification, UserProfile


class ResendAndVerifyEmailPhoneTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('api.auth_views.send_email_otp')
    def test_resend_email_includes_otp_when_email_send_fails(self, mock_send_email):
        # Simulate email send failing but returning an otp
        mock_send_email.return_value = (False, '333333')

        url = '/auth/resend-otp/'
        resp = self.client.post(url, {'identifier': 'test-user@example.com'}, format='json', HTTP_X_APP_MODE='prod', HTTP_X_DEVICE_ID='device-test')
        self.assertEqual(resp.status_code, 200, msg=str(resp.data))
        self.assertIn('otp', resp.data)
        self.assertEqual(resp.data['otp'], '333333')
        self.assertIn('note', resp.data)
        self.assertTrue('Email sending failed' in resp.data['note'])

    def test_verify_email_with_multiple_otps_uses_latest(self):
        identifier = 'verify-me@example.com'

        # Create pending signup
        pending = PendingSignup.objects.create(
            identifier=identifier,
            email=identifier,
            phone_number=None,
            password='hashed_dummy',
            latitude=12.0,
            longitude=77.0,
            interests=[],
            pincode='560001',
            city='Bengaluru',
            state='Karnataka',
            country='India',
            device_id='device-email-test'
        )

        now = timezone.now()
        older = OTPVerification.objects.create(
            identifier=identifier,
            otp_code='444444',
            created_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=4),
            is_verified=False
        )
        newer = OTPVerification.objects.create(
            identifier=identifier,
            otp_code='555555',
            created_at=now,
            expires_at=now + timedelta(minutes=5),
            is_verified=False
        )

        url = '/auth/verify-otp/'
        resp = self.client.post(url, {'identifier': identifier, 'entered_otp': '555555'}, format='json', HTTP_X_DEVICE_ID='device-email-test', HTTP_X_APP_MODE='prod')
        self.assertIn(resp.status_code, (200, 201))

        # Newer OTP should be marked verified
        newer.refresh_from_db()
        self.assertTrue(newer.is_verified)

        # Pending signup should be removed
        self.assertFalse(PendingSignup.objects.filter(identifier=identifier).exists())

        # User should be created with the email
        user_exists = UserProfile.objects.filter(email=identifier).exists()
        self.assertTrue(user_exists)

    @patch('api.auth_views.send_email_otp')
    def test_resend_email_accepts_mixed_case_and_includes_otp_when_send_fails(self, mock_send_email):
        mock_send_email.return_value = (False, '333333')
        url = '/auth/resend-otp/'
        # Use mixed case and trailing space
        resp = self.client.post(url, {'identifier': ' Test-USER@Example.com '}, format='json', HTTP_X_APP_MODE='prod', HTTP_X_DEVICE_ID='device-test')
        self.assertEqual(resp.status_code, 200, msg=str(resp.data))
        self.assertIn('otp', resp.data)
        self.assertEqual(resp.data['otp'], '333333')
        # Identifier in response should be normalized
        self.assertEqual(resp.data['identifier'], 'test-user@example.com')

    def test_verify_email_accepts_mixed_case_identifier(self):
        identifier = 'verify-me@example.com'

        # Create pending signup
        pending = PendingSignup.objects.create(
            identifier=identifier,
            email=identifier,
            phone_number=None,
            password='hashed_dummy',
            latitude=12.0,
            longitude=77.0,
            interests=[],
            pincode='560001',
            city='Bengaluru',
            state='Karnataka',
            country='India',
            device_id='device-email-test'
        )

        now = timezone.now()
        older = OTPVerification.objects.create(
            identifier=identifier,
            otp_code='444444',
            created_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=4),
            is_verified=False
        )
        newer = OTPVerification.objects.create(
            identifier=identifier,
            otp_code='555555',
            created_at=now,
            expires_at=now + timedelta(minutes=5),
            is_verified=False
        )

        url = '/auth/verify-otp/'
        # Send identifier with mixed case and spaces
        resp = self.client.post(url, {'identifier': ' Verify-Me@Example.Com ', 'entered_otp': '555555'}, format='json', HTTP_X_DEVICE_ID='device-email-test', HTTP_X_APP_MODE='prod')
        self.assertIn(resp.status_code, (200, 201))

        # Newer OTP should be marked verified
        newer.refresh_from_db()
        self.assertTrue(newer.is_verified)

        # Pending signup should be removed
        self.assertFalse(PendingSignup.objects.filter(identifier=identifier).exists())

        # User should be created with the email
        user_exists = UserProfile.objects.filter(email=identifier).exists()
        self.assertTrue(user_exists)
