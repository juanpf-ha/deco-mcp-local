"""Actual pinned SDK handshake against synthetic encrypted transport replies."""
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs


@unittest.skipUnless(sys.version_info >= (3, 14), 'SDK requires Python 3.14; Docker runs this test')
class SDKIntegrationTests(unittest.TestCase):
    def test_real_sdk_login_queries_and_guard_without_physical_router(self):
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from tplink_deco_api.crypto.aes import aes_encrypt, aes_decrypt
        from deco_mcp_local.router import Router
        from deco_mcp_local.privacy import Privacy
        from deco_mcp_local.tools import QueryService
        from deco_mcp_local.config import Config

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = key.public_key().public_numbers()
        parts = [format(public.n, 'x'), format(public.e, 'x')]
        operations = []

        class EncryptedPeer:
            def __init__(self, host, pin, timeout):
                self.asserted_host = host

            def post_json(self, url, data):
                if url == 'https://10.23.4.1/cgi-bin/luci/;stok=/login?form=auth':
                    return {'result': {'key': parts, 'seq': 100}}
                if url == 'https://10.23.4.1/cgi-bin/luci/;stok=/login?form=keys':
                    return {'result': {'password': parts}}
                raise AssertionError('Unexpected login destination')

            def post_form(self, url, body):
                fields = parse_qs(body)
                # The SDK splits the signature into RSA blocks. This test key
                # is large enough for one signature block with the fixed fields.
                signature = key.decrypt(bytes.fromhex(fields['sign'][0]), padding.PKCS1v15()).decode()
                secrets = parse_qs(signature)
                aes_key, iv = secrets['k'][0], secrets['i'][0]
                request = json.loads(aes_decrypt(aes_key, iv, fields['data'][0]))
                operations.append(request['operation'])
                if url.endswith('/login?form=login'):
                    password = key.decrypt(bytes.fromhex(request['params']['password']), padding.PKCS1v15()).decode()
                    if password != 'synthetic-password':
                        raise AssertionError('Wrong synthetic credential')
                    result = {'stok': 'aabbccdd', 'usrLvl': 1}
                elif url.endswith('/admin/device?form=device_list'):
                    result = {'device_list': [{'mac': '02-00-00-00-00-01', 'device_ip': '10.23.4.1',
                              'device_model': 'X20', 'software_ver': '1.4.0', 'role': 'master',
                              'inet_status': 'online', 'group_status': 'connected'}]}
                elif url.endswith('/admin/client?form=client_list'):
                    result = {'client_list': [{'mac': '02-00-00-00-00-02', 'ip': '10.23.4.20',
                              'name': 'UHJpdmF0ZSBwaG9uZQ==', 'online': True, 'up_speed': 4,
                              'down_speed': 12, 'access_host': '02-00-00-00-00-01', 'wire_type': 'wireless'}]}
                elif url.endswith('/admin/client?form=addr_reservation'):
                    result = {'reservation_list': [{'mac': '02-00-00-00-00-02', 'ip': '10.23.4.20'}]}
                else:
                    raise AssertionError('Unexpected authenticated destination')
                return {'data': aes_encrypt(aes_key, iv, json.dumps({'error_code': 0, 'result': result}))}

        cfg = Config('10.23.4.1', 'a' * 64, 'synthetic-password', b'a' * 32)
        router = Router(cfg)
        queries = QueryService(router, Privacy(cfg.alias_key))
        with patch('deco_mcp_local.router.PinnedTransport', EncryptedPeer):
            status = queries.call('deco_status', {})
            clients = queries.call('deco_clients', {})
            reservations = queries.call('deco_reservations', {})
            traffic = queries.call('deco_traffic', {})
            with self.assertRaises(ValueError):
                router.call(lambda c: c.request('admin/client', 'client_list', {'operation': 'write'}))
        self.assertEqual(status['nodes'][0]['model'], 'X20')
        self.assertEqual(status['nodes'][0]['id'], clients['clients'][0]['node'])
        self.assertEqual(clients['clients'][0]['id'], reservations['reservations'][0]['id'])
        self.assertEqual(traffic['traffic'][0]['down'], 12)
        self.assertNotIn('write', operations)
        self.assertNotIn('Private', json.dumps([clients, reservations, traffic]))


if __name__ == '__main__':
    unittest.main()
