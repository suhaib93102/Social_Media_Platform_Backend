"""
Utility functions for header validation and device management
"""
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
import uuid
import os


def get_headers(request):
    """
    Extract and validate required headers from request
    Returns: (device_id, app_mode, auth_token, is_valid, error_message)
    """
    # Get device_id (mandatory)
    device_id = request.META.get('HTTP_X_DEVICE_ID', '').strip()
    if not device_id:
        return None, None, None, False, "x-device-id header is required"
    
    # Get app_mode (prod or staging) - default to prod
    app_mode = request.META.get('HTTP_APP_MODE', 'prod').strip().lower()
    if app_mode not in ['prod', 'staging', 'debug', 'release']:
        return device_id, None, None, False, "app-mode must be 'prod', 'staging', 'debug' or 'release'"
    
    # Get authorization token (optional)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '').strip()
    auth_token = None
    if auth_header.startswith('Bearer '):
        auth_token = auth_header.replace('Bearer ', '').strip()
    
    return device_id, app_mode, auth_token, True, None


def get_or_create_guest_user(device_id):
    """
    Find existing guest user by device_id or create new one
    Returns: (user, created)
    """
    try:
        user = UserProfile.objects.get(device_id=device_id)
        return user, False
    except UserProfile.DoesNotExist:
        # Create new guest user
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        user = UserProfile.objects.create(
            userId=guest_id,
            device_id=device_id,
            is_guest=True,
            latitude=None,
            longitude=None
        )
        return user, True


def is_debug_mode(app_mode):
    """
    Check if running in debug mode
    DEBUG: NODE_ENV=development AND app-mode=debug
    """
    env = os.getenv('NODE_ENV', 'development')
    return env == 'development' and app_mode == 'debug'


def get_otp_for_debug_mode(app_mode):
    """
    Return fixed OTP for debug mode
    DEBUG: 123456
    """
    if is_debug_mode(app_mode):
        return '123456'
    return None


def verify_otp_in_debug_or_production(entered_otp, app_mode, actual_otp=None):
    """
    Verify OTP based on mode
    DEBUG: accept '123456'
    PRODUCTION: verify actual_otp
    """
    if is_debug_mode(app_mode):
        # Debug mode: accept fixed OTP
        return str(entered_otp) == '123456'
    else:
        # Production: verify against actual OTP
        return str(entered_otp) == str(actual_otp) if actual_otp else False


def get_otp_message(app_mode):
    """
    Return appropriate message for OTP sending
    """
    if is_debug_mode(app_mode):
        return "Debug mode: Use OTP 123456 (no SMS/Email sent)"
    else:
        return "OTP sent successfully via SMS/Email"
