"""
OTP service for user authentication.
"""

import random
import string
import africastalking
from django.conf import settings
from django.core.cache import cache


def generate_otp():
    """
    Generate a 6-digit OTP.
    
    Returns:
        str: 6-digit OTP code
    """
    return ''.join(random.choices(string.digits, k=6))


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP via Africa's Talking SMS.
    
    Args:
        phone_number (str): Recipient phone number in format +254XXXXXXXXX
        otp_code (str): 6-digit OTP code
    
    Raises:
        Exception: If SMS sending fails
    """
    try:
        username = settings.AT_USERNAME
        api_key = settings.AT_API_KEY
        
        if not api_key or not username:
            raise ValueError('Africa\'s Talking credentials not configured')
        
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        message = f'Your Bima Afya verification code is: {otp_code}. Valid for 10 minutes.'
        
        response = sms.send(
            message=message,
            recipients=[phone_number],
            sender_id=settings.AT_SENDER_ID
        )
        
        if response['SMSMessageData']['Recipients'][0]['statusCode'] != 0:
            raise Exception(f"SMS send failed: {response}")
        
        return response
        
    except Exception as e:
        raise Exception(f"Failed to send OTP SMS: {str(e)}")
