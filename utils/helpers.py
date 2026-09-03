"""
Helper utilities for the AD Manager application.
"""

import re
import hashlib
import secrets
import string
from typing import Optional
from datetime import datetime


def format_ad_date(date_str: str) -> str:
    """Format an AD datetime string to a readable format."""
    if not date_str or date_str == 'None':
        return "N/A"

    try:
        # AD dates can be in various formats
        # Try common formats
        for fmt in [
            '%Y%m%d%H%M%S.%fZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%m/%d/%Y %I:%M:%S %p',
        ]:
            try:
                dt = datetime.strptime(date_str.split('.')[0][:19], fmt.split('.')[0][:19])
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, IndexError):
                continue

        # If nothing works, return a cleaned version
        return date_str[:19] if len(date_str) > 19 else date_str

    except Exception:
        return str(date_str)[:19] if date_str else "N/A"


def format_user_control(uac: int) -> str:
    """Convert UserAccountControl bitmask to readable flags."""
    flags = []
    flag_map = {
        0x1: "SCRIPT",
        0x2: "ACCOUNTDISABLE",
        0x4: "HOMEDIR_REQUIRED",
        0x8: "LOCKOUT",
        0x10: "PASSWD_NOTREQD",
        0x20: "PASSWD_CANT_CHANGE",
        0x40: "ENCRYPTED_PWD_ALLOWED",
        0x80: "TEMP_DUPLICATE_ACCOUNT",
        0x100: "NORMAL_ACCOUNT",
        0x200: "INTERDOMAIN_TRUST_ACCOUNT",
        0x400: "WORKSTATION_TRUST_ACCOUNT",
        0x800: "SERVER_TRUST_ACCOUNT",
        0x1000: "DONT_EXPIRE_PASSWD",
        0x2000: "ACCOUNT_AUTO_LOCKED",
        0x4000: "ENCRYPTED_TEXT_PWD_ALLOWED",
        0x8000: "HOME_DIR_ENABLE",
        0x10000: "LOCKOUT_THRESHOLD",
        0x20000: "LOCKOUT_OBJS_RESET",
        0x40000: "LOCKOUT_DURATION",
        0x80000: "MNS_LOGON_ACCOUNT",
        0x100000: "SMARTCARD_REQUIRED",
        0x200000: "TRUSTED_FOR_DELEGATION",
        0x400000: "NOT_DELEGATED",
        0x800000: "USE_DESN_KEY_ONLY",
        0x1000000: "DONT_REQ_PREAUTH",
        0x2000000: "PASSWORD_EXPIRED",
        0x4000000: "TRUSTED_TO_AUTH_FOR_DELEGATION",
        0x8000000: "PARTIAL_SECRETS_ACCOUNT",
    }

    for flag_value, flag_name in flag_map.items():
        if uac & flag_value:
            flags.append(flag_name)

    return ", ".join(flags) if flags else "NORMAL"


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate a password meets AD complexity requirements.
    Returns (is_valid, message).
    """
    if len(password) < 7:
        return False, "Password must be at least 7 characters long."

    if len(password) > 128:
        return False, "Password must be less than 128 characters."

    checks = {
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digit': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]', password)),
    }

    complexity = sum(checks.values())
    if complexity < 3:
        return False, "Password must contain at least 3 of: uppercase, lowercase, digits, special characters."

    # Check for common passwords
    common_passwords = {
        'password', 'password1', 'welcome', 'letmein', 'admin',
        'changeme', 'abc123', '123456', 'qwerty', 'monkey',
    }
    if password.lower() in common_passwords:
        return False, "This is a commonly used password. Please choose a more secure one."

    return True, "Password meets complexity requirements."


def generate_password(length: int = 16) -> str:
    """Generate a secure random password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"

    # Ensure complexity
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]

    for _ in range(length - 4):
        password.append(secrets.choice(chars))

    # Shuffle
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def extract_cn_from_dn(dn: str) -> str:
    """Extract the Common Name from a Distinguished Name."""
    if not dn:
        return ""
    match = re.match(r'CN=([^,]+)', dn)
    return match.group(1) if match else dn


def extract_ou_from_dn(dn: str) -> str:
    """Extract the last OU from a Distinguished Name."""
    if not dn:
        return ""
    ou_matches = re.findall(r'OU=([^,]+)', dn)
    return ou_matches[-1] if ou_matches else ""


def format_dn_display(dn: str) -> str:
    """Format a DN for display, showing path components."""
    if not dn:
        return ""

    parts = []
    for component in dn.split(','):
        component = component.strip()
        if component.upper().startswith('CN='):
            parts.append(f"👤 {component[3:]}")
        elif component.upper().startswith('OU='):
            parts.append(f"📁 {component[3:]}")
        elif component.upper().startswith('DC='):
            parts.append(component[3:])

    return ' > '.join(parts)


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis if too long."""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text


def get_uac_status_text(uac: int) -> str:
    """Get a brief status text from UAC flags."""
    statuses = []

    if uac & 0x2:
        statuses.append("❌ Disabled")
    else:
        statuses.append("✅ Enabled")

    if uac & 0x100000:
        statuses.append("🔒 Smart Card Required")

    if uac & 0x1000:
        statuses.append("⏰ Password Never Expires")

    if uac & 0x200000:
        statuses.append("🔓 Trusted for Delegation")

    if uac & 0x1000000:
        statuses.append("🔑 No Pre-Auth Required")

    return " | ".join(statuses)


class Signal:
    """Simple signal/slot implementation for loose coupling."""

    def __init__(self):
        self._slots = []

    def connect(self, slot):
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot):
        if slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args, **kwargs):
        for slot in self._slots:
            try:
                slot(*args, **kwargs)
            except Exception as e:
                print(f"Signal slot error: {e}")

    def __len__(self):
        return len(self._slots)
