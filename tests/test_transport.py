"""Exercise real TLS sockets with throwaway certificates; no physical router."""
import hashlib
from pathlib import Path
import socket
import ssl
import tempfile
import threading
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from deco_mcp_local.transport import PinnedTransport, TransportError, inspect_certificate
from deco_mcp_local.router import guard_request


class TLSPeer:
    def __init__(self, response=b'{"result":{}}', status='200 OK'):
        self.tmp = tempfile.TemporaryDirectory()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic-router')])
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
                .sign(key, hashes.SHA256()))
        root = Path(self.tmp.name)
        (root / 'cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        (root / 'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        self.pin = hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.load_cert_chain(root / 'cert.pem', root / 'key.pem')
        self.sock = socket.socket()
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen(1)
        self.sock.settimeout(3)
        self.port = self.sock.getsockname()[1]
        self.received = b''
        self.response, self.status = response, status
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            conn, _ = self.sock.accept()
            with self.ctx.wrap_socket(conn, server_side=True) as tls:
                tls.settimeout(3)
                self.received = tls.recv(65536)
                if self.received:
                    # Consume the complete HTTP request before closing TLS.
                    # A single recv can contain headers without the body;
                    # closing with unread bytes can cause a TCP reset on Windows.
                    while b'\r\n\r\n' not in self.received:
                        chunk = tls.recv(65536)
                        if not chunk:
                            return
                        self.received += chunk
                    head, body = self.received.split(b'\r\n\r\n', 1)
                    length = next((int(line.split(b':', 1)[1].strip())
                                   for line in head.split(b'\r\n')
                                   if line.lower().startswith(b'content-length:')), 0)
                    while len(body) < length:
                        chunk = tls.recv(65536)
                        if not chunk:
                            return
                        body += chunk
                        self.received += chunk
                    headers = ('HTTP/1.1 ' + self.status + '\r\nContent-Type: application/json\r\n'
                               + 'Location: https://external.invalid/\r\nContent-Length: '
                               + str(len(self.response)) + '\r\nConnection: close\r\n\r\n').encode()
                    tls.sendall(headers + self.response)
        except (OSError, ssl.SSLError):
            pass
        finally:
            self.sock.close()

    def close(self):
        self.thread.join(4)
        self.sock.close()
        self.tmp.cleanup()


class TransportTests(unittest.TestCase):
    def peer(self, **kwargs):
        peer = TLSPeer(**kwargs)
        self.addCleanup(peer.close)
        return peer

    def transport(self, peer, pin=None):
        # Keep production address validation. Redirect only TCP destination to a
        # throwaway local TLS peer, below the HTTP/TLS implementation under test.
        transport = PinnedTransport('10.23.4.1', pin or peer.pin, timeout=2)
        real_create = socket.create_connection
        patcher = patch('socket.create_connection',
                        side_effect=lambda address, *a, **kw: real_create(('127.0.0.1', peer.port), *a, **kw))
        patcher.start()
        self.addCleanup(patcher.stop)
        return transport

    def test_wrong_pin_sends_no_http_or_credentials(self):
        peer = self.peer()
        t = self.transport(peer, 'f' * 64)
        with self.assertRaises(TransportError):
            t.post_json('https://10.23.4.1/cgi-bin/luci/;stok=/login?form=auth', {'operation': 'read'})
        peer.thread.join(3)
        self.assertEqual(peer.received, b'')

    def test_certificate_inspection_sends_no_http(self):
        peer = self.peer()
        real_create = socket.create_connection
        with patch('socket.create_connection', side_effect=lambda address, *a, **kw:
                   real_create(('127.0.0.1', peer.port), *a, **kw)):
            self.assertEqual(inspect_certificate('10.23.4.1'), peer.pin)
        peer.thread.join(3)
        self.assertEqual(peer.received, b'')

    def test_tls_fixture_consumes_fragmented_request_before_reply(self):
        peer = self.peer()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection(('127.0.0.1', peer.port), timeout=3) as raw:
            with ctx.wrap_socket(raw, server_hostname='synthetic-router') as tls:
                tls.sendall(b'POST /test HTTP/1.1\r\nHost: synthetic-router\r\nContent-Length:')
                tls.sendall(b' 7\r\n\r\n')
                tls.sendall(b'{"a":1}')
                self.assertIn(b'200 OK', tls.recv(4096))
        peer.thread.join(3)
        self.assertTrue(peer.received.endswith(b'{"a":1}'))

    def test_pinned_request_succeeds_without_environment_proxy(self):
        peer = self.peer()
        t = self.transport(peer)
        with patch.dict('os.environ', {'HTTPS_PROXY': 'http://external.invalid:9999'}):
            result = t.post_json('https://10.23.4.1/cgi-bin/luci/;stok=/login?form=auth', {'operation': 'read'})
        self.assertEqual(result, {'result': {}})
        self.assertIn(b'POST /cgi-bin/', peer.received)

    def test_redirect_is_rejected(self):
        peer = self.peer(status='302 Found')
        with self.assertRaises(TransportError):
            self.transport(peer).post_json('https://10.23.4.1/cgi-bin/luci/;stok=/login?form=auth', {})

    def test_arbitrary_destinations_and_paths_fail_without_socket(self):
        t = PinnedTransport('10.23.4.1', 'f' * 64)
        with patch('socket.create_connection', side_effect=AssertionError('network forbidden')):
            for url in ['https://8.8.8.8/', 'http://10.23.4.1/',
                        'https://10.23.4.1:444/cgi-bin/luci/;stok=/login?form=auth',
                        'https://10.23.4.1/cgi-bin/luci/;stok=x/admin/system?form=reboot',
                        'https://10.23.4.1/cgi-bin/luci/;stok=/login?form=auth#fragment']:
                with self.subTest(url=url), self.assertRaises(TransportError):
                    t.post_json(url, {})

    def test_rejects_huge_or_non_object_response(self):
        for data in [b'[]', b'x' * (2 * 1024 * 1024 + 1)]:
            peer = self.peer(response=data)
            with self.assertRaises(TransportError):
                self.transport(peer).post_json('https://10.23.4.1/cgi-bin/luci/;stok=/login?form=auth', {})
            # Finish each patch before the next case, avoiding nested redirects.
            self.doCleanups()

    def test_guard_denies_writes_and_unknown_reads(self):
        for args in [('admin/client', 'client_list', {'operation': 'write'}),
                     ('admin/wireless', 'wlan', {'operation': 'read'}),
                     ('admin/device', 'device_list', {'operation': 'reboot'})]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                guard_request(*args)
        guard_request('admin/device', 'device_list', {'operation': 'read'})
        guard_request('admin/client', 'addr_reservation', {'operation': 'getlist'})


if __name__ == '__main__':
    unittest.main()
