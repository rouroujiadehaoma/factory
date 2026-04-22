"""Security utility functions"""
import re

def mask_phone(phone):
    """Mask phone number"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '****' + phone[-4:]

def mask_email(email):
    """Mask email address"""
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    username = parts[0]
    if len(username) <= 2:
        masked = '*' * len(username)
    else:
        masked = username[0] + '*' * (len(username) - 2) + username[-1]
    return masked + '@' + parts[1]

def validate_ucd_email(email):
    """Validate UCD email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@ucdconnect\.ie$'
    return bool(re.match(pattern, email))

