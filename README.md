# deco-mcp-local

**Read-only TP-Link Deco MCP over SSH/stdio, with certificate pinning and
pseudonymized device identifiers.** Run it on your own Linux/Docker machine,
including an x86 thin client. No open MCP port or TP-Link cloud login.

[Guía en español](README.es.md) · [Security model](SECURITY.md) ·
[Contributing](CONTRIBUTING.md) · [Upstream attribution](NOTICE.md)

Experimental: not affiliated with TP-Link. The local router API is undocumented.
No physical router model is certified by this release. A passing simulator test
is not a claim of X20/M5 or other firmware compatibility.

## What it does

| Tool | Output |
|---|---|
| `deco_status` | Mesh node models, firmware, role and connection state |
| `deco_clients` | Paginated devices, online state, connection and node |
| `deco_reservations` | Paginated fixed DHCP assignments |
| `deco_traffic` | Paginated online device traffic, busiest first |

No reboot, renaming, reservations writes, raw requests, raw configuration, SSIDs
or Wi-Fi passwords. Default output omits names and replaces MAC/IP with stable
HMAC aliases; node/device aliases correlate across tools. A fresh key changes
all aliases. This is **pseudonymization**, not full anonymization.

**Privacy boundary:** the server has no telemetry, but results go to your MCP
client. A cloud AI client may send those results to its provider. Models,
firmware, topology, rates and timing still disclose information.

## Requirements

- Linux x86_64 or ARM64 with Docker Engine and Docker Compose.
- Router reachable on TCP 443 using TLS 1.2+, on an RFC1918 IPv4 address.
- Deco owner password and an independently verified router certificate SHA-256.
- An MCP client with stdio support; SSH for a separate server.
- Python 3.14 inside the container; the interactive enrollment script works with
  Ubuntu's Python 3.10+ on the host.

Using a single primary Deco to enumerate its mesh is the intended architecture;
each model/firmware must be tested. Some firmware reports unknown fields or
client-node associations; the server emits `unknown`/`null` instead of guessing.

## Install on your Linux host

Download this repository and open its directory. Review source and SECURITY.md
before providing credentials. Do not run a downloaded installer as root.

```sh
docker build --target runtime -t deco-mcp-local:0.1.0 .
docker build --target test -t deco-mcp-local-test:0.1.0 .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges deco-mcp-local-test:0.1.0
```

Inspect a certificate without logging in (the address below is synthetic):

```sh
docker run --rm --read-only --cap-drop ALL deco-mcp-local:0.1.0 \
  --inspect-certificate 10.23.4.1
```

Verify the displayed fingerprint through a trusted path, such as comparing the
certificate independently on a trusted connection to the router. Merely copying
an observed fingerprint does not protect first enrollment against an existing
attacker. An equivalent OpenSSL inspection hashes DER bytes of the leaf cert:

```sh
openssl s_client -connect 10.23.4.1:443 </dev/null 2>/dev/null \
  | openssl x509 -outform DER | openssl dgst -sha256
```

Then enroll **in a terminal on the server**, never by sending your password to
the AI chat or placing it in a shell argument:

```sh
python3 scripts/enroll.py
chmod 755 scripts/run-mcp.sh
docker compose run --rm -T --no-deps deco-mcp --check
```

Enrollment creates ignored `.env` and `secrets/` files. The secret directory is
0700, secret files 0444 for Docker's unprivileged UID, and `.env` 0600. Keep
parent directories private: root/Docker administrators can still read secrets.
The script refuses to overwrite an existing enrollment. To rotate, back up the
old files outside the repository, verify a new pin, then enroll deliberately.
Partial enrollment after disk/permission failure needs local inspection.

Do not use `docker compose up -d`: this is an on-demand stdio process. Your MCP
client starts it, and EOF stops it. No persistent service or port forwarding.
The first Compose run creates a project-specific Docker bridge network.

## Connect from Codex or another MCP client

Configure key-based SSH, verify the SSH host key independently, then use the
template in [examples/codex-config.toml](examples/codex-config.toml). Replace
placeholders locally. SSH must use `-T` so a terminal does not alter protocol IO.
The remote command is the absolute path to `scripts/run-mcp.sh`.

Codex MCP docs: https://developers.openai.com/codex/mcp/

The SSH operator must be allowed to run Docker. Membership in the Docker group
is effectively root access; for a shared deployment use a dedicated restricted
SSH entry/forced command reviewed by its administrator. The MCP process does
not need the Docker socket mounted inside its container.

Example prompts: “Show mesh status”; “List online devices”; “Which aliases are
using the most bandwidth?” Pagination arguments: `limit` 1–100 (default 25),
`offset` 0–100000. `deco_clients` also accepts boolean `online_only`.

Traffic units are passed through from firmware and may vary; they are not a
browsing-history record or packet capture. Pages are fresh snapshots, so device
membership or traffic ordering can change between requests.

## Optional identifying output

For local troubleshooting only, the operator may set
`DECO_REVEAL_IDENTIFIERS=1` in ignored `.env`. This deliberately exposes device
names, MACs and IPs to the client/model; outputs say `identifiers_visible`.
Tool arguments cannot enable this mode. Treat names as untrusted data and never
upload these outputs as GitHub examples. Default mode is recommended.

## Security and reproducibility

- Certificate pin verified before HTTP headers/body; mismatch fails closed.
- No environment proxies or redirects; only one configured private IPv4 target
  and three SDK read endpoints. No generic network-request tool.
- Strict arguments, bounded protocol/router payloads, generic error responses,
  no runtime credential logging; logging by the SDK is disabled in the CLI.
- Non-root container, read-only filesystem, no capabilities, CPU/RAM/PID limits,
  no published ports and no Docker socket.
- Pinned runtime packages with hash checking. Source dependency provenance is in
  NOTICE.md. The Python base image is pinned by digest; review updates before
  changing the digest. No automatic updates occur at runtime.

Application destination checks are **not** an OS egress firewall against
arbitrary malicious dependency code. Use a dedicated VM/VLAN/firewall if you
need this guarantee; builds need registry access but runtime only needs the
router. We do not alter a shared host's firewall or home automation services.

## Troubleshooting

- **Certificate mismatch:** stop and independently verify. Never disable pinning.
- **Authentication failure:** check password locally. Owner account password may
  be shared with your Deco app account; do not reuse it elsewhere.
- **Timeout/disconnect:** check host Wi-Fi, SSH and router reachability. No
  automatic login retry avoids repeated login attempts or possible lockouts.
- **Unknown node/state:** firmware/API mismatch; report only sanitized symptoms.
- **Multiple admin sessions:** do not run clients in parallel or poll rapidly.
  SDK logout invalidates local token state; it does not revoke the router session.
- **TLS failure:** old/self-signed is supported via pin, but TLS older than 1.2 is
  deliberately rejected. There is no insecure bypass flag.

## Tests and publication

`python -m unittest discover -s tests -v` from repository root, with Python 3.14
and the locked runtime dependencies. Docker tests run offline against generated
TLS peers and synthetic encrypted SDK responses, never your actual router.

Before pushing, review the complete Git history as well as current files.
Never include `.env`, secret files, real logs, names, addresses, SSH configuration
or backups. Publishing source does not require publishing local enrollment.
Enable private vulnerability reporting in the eventual GitHub repository.

License: MIT. Preserve LICENSE and NOTICE.md when redistributing.
