"""Operator-only configuration. Secrets are never accepted on the command line."""
from dataclasses import dataclass, field
import ipaddress
import os
from pathlib import Path
import re
import stat


class ConfigError(ValueError):
    pass


def private_host(value):
    try:
        addr = ipaddress.IPv4Address(value)
        if any(addr in ipaddress.ip_network(net) for net in
               ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
            return str(addr)
    except (ValueError, TypeError):
        pass
    raise ConfigError('DECO_HOST must be an RFC1918 IPv4 address')


def read_secret(name):
    try:
        path = Path(os.environ[name])
        # O_NOFOLLOW blocks final-component symlinks on POSIX. Parent directories
        # must remain operator-controlled; Docker secret mounts may be 0444.
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 4096:
                raise ValueError
            value = stream.read(4097).decode('utf-8').rstrip('\r\n')
        if not value or len(value) > 4096 or '\n' in value or '\r' in value or '\x00' in value:
            raise ValueError
        return value
    except (OSError, KeyError, ValueError, UnicodeError):
        raise ConfigError(f'{name} must reference a readable secret file') from None


@dataclass(frozen=True)
class Config:
    host: str
    pin: str
    password: str = field(repr=False)
    alias_key: bytes = field(repr=False)
    reveal_identifiers: bool = False
    timeout: float = 45.0

    @classmethod
    def from_env(cls):
        host = private_host(os.environ.get('DECO_HOST', ''))
        pin = os.environ.get('DECO_TLS_SHA256', '').lower()
        if not re.fullmatch('[a-f0-9]{64}', pin):
            raise ConfigError('DECO_TLS_SHA256 must be a verified SHA-256 certificate fingerprint')
        reveal = os.environ.get('DECO_REVEAL_IDENTIFIERS', '0')
        if reveal not in ('0', '1'):
            raise ConfigError('DECO_REVEAL_IDENTIFIERS must be 0 or 1')
        try:
            timeout = int(os.environ.get('DECO_TIMEOUT_SECONDS', '45'))
            if not 1 <= timeout <= 60:
                raise ValueError
        except ValueError:
            raise ConfigError('DECO_TIMEOUT_SECONDS must be an integer from 1 to 60') from None
        password = read_secret('DECO_PASSWORD_FILE')
        key = read_secret('DECO_ALIAS_KEY_FILE')
        if not re.fullmatch('[a-fA-F0-9]{64}', key):
            raise ConfigError('DECO_ALIAS_KEY_FILE must contain 32 random bytes encoded as 64 hex characters')
        return cls(host, pin, password, bytes.fromhex(key), reveal == '1', timeout)
