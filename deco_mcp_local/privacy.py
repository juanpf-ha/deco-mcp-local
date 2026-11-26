"""Explicit output transformations, never recursive best-effort secret filtering."""
import hashlib
import hmac
import ipaddress
import re


class Privacy:
    def __init__(self, key, reveal=False):
        self.key, self.reveal = key, reveal

    def _alias(self, kind, value):
        digest = hmac.new(self.key, f'{kind}:{value}'.encode(), hashlib.sha256).hexdigest()[:16]
        return f'{kind}-{digest}'

    def device(self, value):
        value = str(value or '').upper().replace('-', ':')
        if not re.fullmatch(r'(?:[0-9A-F]{2}:){5}[0-9A-F]{2}', value):
            return None
        return value if self.reveal else self._alias('device', value)

    def address(self, value):
        try:
            value = str(ipaddress.ip_address(value))
        except (ValueError, TypeError):
            return None
        return value if self.reveal else self._alias('address', value)

    def name(self, value):
        # Names can contain prompt injection. Omit entirely in the default mode.
        return str(value or '')[:64] if self.reveal else None


def token(value, pattern=r'[A-Za-z0-9_.-]{1,32}'):
    value = str(value or '')
    return value if re.fullmatch(pattern, value) else 'unknown'


def choice(value, allowed):
    return value if isinstance(value, str) and value in allowed else 'unknown'


def rate(value):
    # Router values are untrusted, including NaN/Infinity/negative values.
    import math
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1e15:
        return 0
    return value
