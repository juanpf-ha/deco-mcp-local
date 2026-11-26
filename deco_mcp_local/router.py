"""Constrain the reviewed SDK to three read endpoints."""
from .transport import PinnedTransport, READ_ENDPOINTS


def guard_request(path, form, data):
    if (not isinstance(data, dict) or READ_ENDPOINTS.get((path, form)) is None
            or data.get('operation') != READ_ENDPOINTS[(path, form)]):
        raise ValueError('Only supported read operations are permitted')


class Router:
    def __init__(self, cfg):
        self.cfg = cfg

    def call(self, fn):
        from tplink_deco_api import DecoClient

        class ReadClient(DecoClient):
            def request(self, path, form, data):
                guard_request(path, form, data)
                return super().request(path, form, data)

            def request_list(self, path, form, data):
                guard_request(path, form, data)
                return super().request_list(path, form, data)

        client = ReadClient(self.cfg.host, 'admin', self.cfg.password, timeout=self.cfg.timeout)
        # Private SDK integration intentionally pinned to 2.1.1; integration
        # tests verify login + encrypted replies using that actual SDK.
        client._transport = PinnedTransport(self.cfg.host, self.cfg.pin, self.cfg.timeout)
        try:
            client.login()
            return fn(client)
        finally:
            # SDK logout invalidates local state; it does not revoke the router
            # session remotely. Never claim a server-side logout has occurred.
            client.logout()
