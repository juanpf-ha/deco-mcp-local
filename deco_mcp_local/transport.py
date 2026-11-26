"""Pinned HTTPS, one configured RFC1918 address, no proxies or redirects."""
import hashlib
import hmac
import http.client
import json
import re
import ssl
from urllib.parse import urlsplit

from .config import private_host

MAX_RESPONSE = 2 * 1024 * 1024
READ_ENDPOINTS = {
    ('admin/device', 'device_list'): 'read',
    ('admin/client', 'client_list'): 'read',
    ('admin/client', 'addr_reservation'): 'getlist',
}


class TransportError(RuntimeError):
    pass


def tls_context():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # A private Deco cert is authenticated by mandatory pin, not a public CA.
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


class PinnedConnection(http.client.HTTPSConnection):
    def __init__(self, host, pin, timeout):
        super().__init__(host, timeout=timeout, context=tls_context())
        self.pin = pin

    def connect(self):
        super().connect()
        digest = hashlib.sha256(self.sock.getpeercert(binary_form=True)).hexdigest()
        if not hmac.compare_digest(digest, self.pin):
            self.close()
            raise TransportError('Router certificate mismatch; verify the certificate locally')


class PinnedTransport:
    def __init__(self, host, pin, timeout=10):
        self.host = private_host(host)
        if not isinstance(pin, str) or not re.fullmatch('[a-f0-9]{64}', pin):
            raise ValueError('Invalid certificate pin')
        self.pin, self.timeout, self.cookie = pin, timeout, None

    def post_json(self, url, body):
        return self._post(url, json.dumps(body).encode())

    def post_form(self, url, body):
        return self._post(url, body.encode())

    def _path(self, url):
        try:
            parsed = urlsplit(url)
            if (parsed.scheme != 'https' or parsed.netloc != self.host
                    or parsed.fragment or parsed.username or parsed.password):
                raise ValueError
            match = re.fullmatch(r'/cgi-bin/luci/;stok=([A-Za-z0-9]*)/(login|admin/[a-z_]+)', parsed.path)
            if not match:
                raise ValueError
            stok, endpoint = match.groups()
            if endpoint == 'login':
                if stok or parsed.query not in ('form=auth', 'form=keys', 'form=login'):
                    raise ValueError
            elif not stok or (endpoint, parsed.query.removeprefix('form=')) not in READ_ENDPOINTS:
                raise ValueError
            return parsed.path + '?' + parsed.query
        except (ValueError, TypeError):
            raise TransportError('Router destination or endpoint rejected') from None

    def _post(self, url, data):
        path = self._path(url)
        conn = PinnedConnection(self.host, self.pin, self.timeout)
        try:
            # Verify before request() may transmit headers/body. connect() is
            # also overridden so any automatic reconnection rechecks the pin.
            conn.connect()
            # Each SDK operation uses a fresh connection. Match urllib's
            # explicit one-shot semantics: some Deco firmware resets or stalls
            # client-list replies when the request implies keep-alive.
            headers = {'Content-Type': 'application/json'}
            if self.cookie:
                headers['Cookie'] = self.cookie
            # Keep the session cookie before the final connection header, as
            # urllib does, to reproduce the tested reference request exactly.
            headers['Connection'] = 'close'
            conn.request('POST', path, body=data, headers=headers)
            resp = conn.getresponse()
            if resp.status != 200:
                raise TransportError('Router returned a non-success HTTP status')
            content = resp.read(MAX_RESPONSE + 1)
            if len(content) > MAX_RESPONSE:
                raise TransportError('Router response too large')
            result = json.loads(content)
            if not isinstance(result, dict):
                raise TransportError('Invalid router response')
            for header, value in resp.getheaders():
                if header.lower() == 'set-cookie':
                    match = re.search(r'(?:^|;\s*)(sysauth=[a-f0-9]+)(?:;|$)', value)
                    if match:
                        self.cookie = match[1]
            return result
        except TransportError:
            raise
        except Exception:
            raise TransportError('Router communication failed') from None
        finally:
            conn.close()


def inspect_certificate(host):
    """Inspect only: no HTTP, cookie, login or password. Not an identity proof."""
    host = private_host(host)
    conn = http.client.HTTPSConnection(host, timeout=10, context=tls_context())
    try:
        conn.connect()
        return hashlib.sha256(conn.sock.getpeercert(binary_form=True)).hexdigest()
    finally:
        conn.close()
