"""Allowlisted, bounded read tools inspired by nitin23c/deco-mcp (MIT)."""
from .privacy import choice, rate, token

PAGINATION = {'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 25},
              'offset': {'type': 'integer', 'minimum': 0, 'default': 0}}
TOOLS = [
    ('deco_status', 'Read mesh models, firmware, role and status. Identifiers are pseudonymized by default.', {}),
    ('deco_clients', 'List devices with stable aliases and their node. Names omitted by default.',
     PAGINATION | {'online_only': {'type': 'boolean', 'default': False}}),
    ('deco_traffic', 'Read per-device traffic rates as reported by firmware; units are firmware-dependent.', PAGINATION),
    ('deco_reservations', 'List DHCP reservations using device and address aliases by default.', PAGINATION),
]


class QueryService:
    def __init__(self, router, privacy):
        self.router, self.privacy = router, privacy

    def call(self, name, args):
        specs = {n: props for n, _, props in TOOLS}
        if not isinstance(name, str) or name not in specs or not isinstance(args, dict):
            raise ValueError('Unknown tool or invalid arguments')
        if any(k not in specs[name] for k in args):
            raise ValueError('Unsupported argument')
        for key in ('limit', 'offset'):
            if key in args and (type(args[key]) is not int or args[key] < (1 if key == 'limit' else 0)
                                or args[key] > (100 if key == 'limit' else 100000)):
                raise ValueError('Invalid pagination')
        if 'online_only' in args and type(args['online_only']) is not bool:
            raise ValueError('online_only must be boolean')
        return self.router.call(lambda deco: self._query(deco, name, args))

    def _identity(self, obj):
        p = self.privacy
        out = {'id': p.device(obj.mac), 'address': p.address(obj.ip)}
        if p.reveal:
            out['name'] = p.name(obj.name)
        return out

    def _page(self, key, rows, args):
        offset, limit = args.get('offset', 0), args.get('limit', 25)
        return {'privacy': 'identifiers_visible' if self.privacy.reveal else 'pseudonymized',
                'total': len(rows), key: rows[offset:offset + limit],
                'next_offset': offset + limit if offset + limit < len(rows) else None}

    def _query(self, deco, name, args):
        p = self.privacy
        if name == 'deco_status':
            nodes = []
            for node in deco.get_device_list()[:64]:
                row = {'id': p.device(node.mac), 'address': p.address(node.device_ip),
                       'model': token(node.device_model, r'[A-Za-z0-9_.()-]{1,32}'),
                       'hardware': token(node.hardware_ver),
                       'firmware': token(node.software_ver, r'[A-Za-z0-9_. ()-]{1,96}'),
                       'role': choice(node.role, ('master', 'slave', 'gateway', 'satellite')),
                       'internet': choice(node.inet_status, ('online', 'offline', 'connected', 'disconnected')),
                       'group': choice(node.group_status, ('connected', 'disconnected', 'online', 'offline'))}
                if p.reveal:
                    row['name'] = p.name(node.custom_nickname or node.nickname)
                nodes.append(row)
            return {'privacy': 'identifiers_visible' if p.reveal else 'pseudonymized', 'nodes': nodes}
        if name == 'deco_reservations':
            table = deco.address_reservations.get_table()
            rows = [{'id': p.device(r.mac), 'address': p.address(r.ip)} for r in table.reservations]
            rows.sort(key=lambda r: r['id'] or '')
            return self._page('reservations', rows, args)
        devices = deco.get_client_list()
        rows = []
        for c in devices:
            if not p.device(c.mac) or (args.get('online_only', False) and not c.online):
                continue
            row = self._identity(c)
            row['online'] = bool(c.online)
            if name == 'deco_traffic':
                if not c.online:
                    continue
                row.update(up=rate(c.up_speed), down=rate(c.down_speed))
            else:
                row.update(node=p.device(c.access_host), connection=choice(c.wire_type or c.connection_type,
                           ('wired', 'wireless', 'ethernet', 'wifi', '2.4G', '5G', '6G', '2.4GHz', '5GHz', '6GHz')))
            rows.append(row)
        rows.sort(key=lambda r: r['id'] or '')
        if name == 'deco_traffic':
            rows.sort(key=lambda r: r['up'] + r['down'], reverse=True)
        return self._page('traffic' if name == 'deco_traffic' else 'clients', rows, args)
