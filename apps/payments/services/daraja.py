"""
Daraja M-Pesa API integration wrapper.
"""

import requests
import base64
from datetime import datetime
from django.conf import settings
from django.utils import timezone


class DarajaClient:
    """Wrapper for Safaricom Daraja M-Pesa API."""
    
    BASE_URL = "https://sandbox.safaricom.co.ke" if settings.DEBUG else "https://api.safaricom.co.ke"
    
    def __init__(self):
        self.consumer_key = settings.DARAJA_CONSUMER_KEY
        self.consumer_secret = settings.DARAJA_CONSUMER_SECRET
        self.shortcode = settings.DARAJA_SHORTCODE
        self.passkey = settings.DARAJA_PASSKEY
        self.access_token = None
        self.token_expires_at = None

    def _validate_stk_push_config(self):
        """Validate STK Push settings before calling Daraja."""
        callback_url = getattr(settings, 'DARAJA_CALLBACK_URL', '').strip()
        if not callback_url:
            raise ValueError('DARAJA_CALLBACK_URL is not set')
        if callback_url.startswith('http://localhost') or callback_url.startswith('http://127.0.0.1'):
            raise ValueError('DARAJA_CALLBACK_URL must be a public HTTPS URL, not localhost')
        if 'your-ngrok-url' in callback_url:
            raise ValueError('DARAJA_CALLBACK_URL is still a placeholder. Set it to a public HTTPS callback URL')
        if not callback_url.startswith('https://'):
            raise ValueError('DARAJA_CALLBACK_URL must use HTTPS')
        return callback_url
    
    def get_access_token(self):
        """Get OAuth 2.0 access token from Daraja."""
        if self.access_token and self.token_expires_at and timezone.now() < self.token_expires_at:
            return self.access_token
        
        url = f"{self.BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        
        headers = {"Authorization": f"Basic {credentials}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data['access_token']
            # Token expires in 3600 seconds, set expiry 5 min before
            self.token_expires_at = timezone.now() + timezone.timedelta(seconds=3595)
            return self.access_token
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to get access token: {str(e)}")
    
    def stk_push(self, phone_number, amount, reference, description):
        """
        Initiate STK push payment request (C2B).
        
        Args:
            phone_number: Customer phone in format 254XXXXXXXXX
            amount: Amount in KES (integer)
            reference: Transaction reference ID
            description: Payment description
        
        Returns:
            dict with CheckoutRequestID and ResponseCode
        """
        callback_url = self._validate_stk_push_config()
        token = self.get_access_token()
        
        url = f"{self.BASE_URL}/mpesa/stkpush/v1/processrequest"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": str(reference),
            "TransactionDesc": description
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            try:
                data = response.json()
            except ValueError:
                data = {'raw_response': response.text}

            if response.status_code >= 400:
                raise ValueError(
                    f"STK push rejected by Daraja: {data.get('errorMessage') or data.get('raw_response') or response.text}"
                )

            return data
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"STK push failed: {str(e)}")
    
    def check_transaction_status(self, checkout_request_id):
        """Query transaction status using CheckoutRequestID."""
        token = self.get_access_token()
        
        url = f"{self.BASE_URL}/mpesa/stkpushquery/v1/query"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Status check failed: {str(e)}")
    
    def b2c_payout(self, phone_number, amount, reference, description):
        """
        Send money to customer (B2C - Business to Customer).
        Used for claim payouts.
        
        Args:
            phone_number: Recipient phone in format 254XXXXXXXXX
            amount: Amount in KES
            reference: Transaction reference
            description: Reason for payment
        
        Returns:
            dict with ConversationID and ResponseCode
        """
        token = self.get_access_token()
        
        url = f"{self.BASE_URL}/mpesa/b2c/v1/paymentrequest"
        
        payload = {
            "InitiatorName": "testapi",
            "SecurityCredential": settings.DARAJA_SECURITY_CREDENTIAL,
            "CommandID": "SalaryPayment",  # Or BusinessPayment, PromotionPayment
            "Amount": int(amount),
            "PartyA": self.shortcode,
            "PartyB": phone_number,
            "Remarks": description,
            "QueueTimeOutURL": settings.DARAJA_CALLBACK_URL,
            "ResultURL": settings.DARAJA_CALLBACK_URL,
            "Occasion": reference
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"B2C payout failed: {str(e)}")
