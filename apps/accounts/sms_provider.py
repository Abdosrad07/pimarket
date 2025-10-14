"""
SMS Provider Module - Pluggable SMS sending interface

TODO: Configure your SMS provider in .env:
- For Twilio: Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
- For MTN: Set MTN_API_KEY, MTN_API_SECRET

Currently supports:
- Twilio (production ready)
- Mock (for development/testing)
"""

from django.conf import settings


def send_sms(phone_number, message):
    """
    Send SMS using configured provider
    
    Args:
        phone_number (str): Recipient phone number
        message (str): SMS message content
    
    Returns:
        bool: True if sent successfully
    
    Raises:
        Exception: If SMS sending fails
    """
    provider = settings.SMS_PROVIDER.lower()
    
    if provider == 'twilio':
        return send_via_twilio(phone_number, message)
    elif provider == 'mtn':
        return send_via_mtn(phone_number, message)
    else:
        # Mock provider for development
        return send_via_mock(phone_number, message)


def send_via_twilio(phone_number, message):
    """Send SMS via Twilio"""
    try:
        from twilio.rest import Client
        
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_PHONE_NUMBER
        
        if not all([account_sid, auth_token, from_number]):
            raise ValueError("Twilio credentials not configured")
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        
        print(f"SMS sent via Twilio: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Twilio SMS error: {e}")
        raise


def send_via_mtn(phone_number, message):
    """
    Send SMS via MTN API
    
    TODO: Implement MTN API integration
    - Get API credentials from MTN Developer Portal
    - Implement authentication flow
    - Make API call to send SMS
    """
    import requests
    
    # Placeholder implementation
    api_key = getattr(settings, 'MTN_API_KEY', None)
    api_secret = getattr(settings, 'MTN_API_SECRET', None)
    
    if not api_key or not api_secret:
        raise ValueError("MTN credentials not configured")
    
    # TODO: Replace with actual MTN API endpoint and payload
    # endpoint = "https://api.mtn.com/v1/sms/send"
    # headers = {
    #     "Authorization": f"Bearer {api_key}",
    #     "Content-Type": "application/json"
    # }
    # payload = {
    #     "to": phone_number,
    #     "message": message
    # }
    # response = requests.post(endpoint, json=payload, headers=headers)
    # response.raise_for_status()
    
    print(f"MTN SMS (mock): Would send '{message}' to {phone_number}")
    return True


def send_via_mock(phone_number, message):
    """Mock SMS sender for development/testing"""
    print("=" * 50)
    print("MOCK SMS PROVIDER")
    print(f"To: {phone_number}")
    print(f"Message: {message}")
    print("=" * 50)
    return True