from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse
from datetime import timedelta

from api.models import PendingSignup, OTPVerification
from api.auth_views import validate_phone_number


class VerifyOTPMultipleRecordsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Normalize the phone identifier the same way the view does
        is_valid, normalized = validate_phone_number('9310270910')
        assert is_valid
        self.identifier = normalized

        # Create pending signup corresponding to the identifier
        self.pending = PendingSignup.objects.create(
            identifier=self.identifier,
            email=None,
            phone_number=self.identifier,
            password='hashed_dummy',
            latitude=12.0,
            longitude=77.0,
            interests=[],
            pincode='560001',
            city='Bengaluru',
            state='Karnataka',
            country='India',
            device_id='device-test'
        )

        # Create two OTP records for same identifier (older and newer)
        now = timezone.now()
        self.older_otp = OTPVerification.objects.create(
            identifier=self.identifier,
            otp_code='111111',
            created_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=4),
            is_verified=False
        )
        self.newer_otp = OTPVerification.objects.create(
            identifier=self.identifier,
            otp_code='222222',
            created_at=now,
            expires_at=now + timedelta(minutes=5),
            is_verified=False
        )

    def test_verify_with_multiple_otps_uses_latest_and_returns_200(self):
        url = reverse('verify-otp') if 'verify-otp' in [u.name for u in self.client.get('/').wsgi_request.resolver_match.app_names] else '/auth/verify-otp/'
        resp = self.client.post(url, {'identifier': self.identifier, 'entered_otp': '222222'}, format='json', HTTP_X_DEVICE_ID='device-test', HTTP_X_APP_MODE='prod')
        # Should not return 500 and should complete registration (200 OK or 201 depending on implementation)
        self.assertIn(resp.status_code, (200, 201), msg=f"Unexpected status code: {resp.status_code}, content: {resp.content}")
        # The newer OTP should be marked verified
        self.newer_otp.refresh_from_db()
        self.assertTrue(self.newer_otp.is_verified)
        # Pending signup should be deleted
        self.assertFalse(PendingSignup.objects.filter(identifier=self.identifier).exists())
