#!/usr/bin/env python3
"""Interactive Linux enrollment: secrets stay outside Git and container image."""
import getpass
import ipaddress
import os
from pathlib import Path
import re
import secrets
import stat
import sys


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Run in a local terminal or ssh -t. Never pass the password as an argument.')
    root = Path(__file__).resolve().parents[1]
    host = input('Router RFC1918 IPv4 address: ').strip()
    addr = ipaddress.IPv4Address(host)
    if not any(addr in ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
        raise SystemExit('A private IPv4 address is required.')
    pin = input('Independently verified certificate SHA-256 (64 hex): ').strip().lower()
    if not re.fullmatch('[a-f0-9]{64}', pin):
        raise SystemExit('Invalid certificate fingerprint.')
    password = getpass.getpass('Deco owner password (hidden, stored locally): ')
    if not password or any(c in password for c in '\r\n\x00') or len(password.encode()) > 4096:
        raise SystemExit('Invalid password format.')
    os.umask(0o077)
    target = root / 'secrets'
    if target.is_symlink():
        raise SystemExit('Refusing symlink secrets directory.')
    target.mkdir(mode=0o700, exist_ok=True)
    if target.stat().st_uid != os.getuid():
        raise SystemExit('Secrets directory must belong to the current operator.')
    target.chmod(0o700)
    # Refuse replacement, including symlinks. Rotation must be deliberate.
    paths = [target / 'deco_password', target / 'alias_key', root / '.env']
    if any(p.exists() or p.is_symlink() for p in paths):
        raise SystemExit('Enrollment already exists; back it up outside Git and rotate deliberately.')
    values = [password + '\n', secrets.token_hex(32) + '\n',
              f'DECO_HOST={host}\nDECO_TLS_SHA256={pin}\nDECO_REVEAL_IDENTIFIERS=0\n']
    for path, value in zip(paths, values):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(value)
        # Non-root container UID needs read access. The 0700 parent prevents
        # ordinary host users from traversing it; do not copy files elsewhere.
        if path.parent == target:
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print('Enrollment saved locally. No credentials were transmitted by this script.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError):
        raise SystemExit('Enrollment failed; inspect local permissions and partial files without sharing their contents.') from None
