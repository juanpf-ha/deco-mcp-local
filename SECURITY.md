# Security model

This is experimental community software, not affiliated with TP-Link.

## Data flow

MCP client -> SSH/stdio -> local container -> configured private router over
certificate-pinned HTTPS. Results return through stdio. Your AI client may send
these results to its provider. Pseudonyms, models, firmware, topology, counts,
traffic and timing can still reveal information. There is no claim of complete
anonymity, and detailed mode deliberately reveals names/MAC/IP.

No listener, telemetry, cloud login or automatic updater exists in the runtime.
Builds download the Python base image and locked dependencies. CI contacts
GitHub and dependency registries. These are separate from router queries.

## Trust and credentials

An operator must verify the observed certificate fingerprint through a trusted
path before enrollment. Inspection alone is trust-on-first-use and cannot prove
the router identity against an attacker already present. Fail closed on pin
change; re-verify after router replacement or firmware certificate regeneration.

Credentials reside in local files and process memory. Root, the Docker daemon,
the host operator and anyone with equivalent privileges can read them. Docker
group membership is effectively root access. File mounts are not an encrypted
secret store. Protect backups, host disk and parent directory permissions.

The HMAC alias key is a separate random secret. Keep it stable for cross-tool
correlation; rotating it changes aliases. Do not publish it or real output.

## Read-only boundary

There are no write tools. An SDK guard permits only device list read, client list
read and reservation getlist. The HTTPS transport separately restricts address
and endpoint paths. Login creates an admin session and can interfere with other
admin logins. SDK logout clears local state without remote session revocation.
Avoid polling or running multiple sessions in parallel.

The transport ignores proxy environment variables, never follows redirects,
caps response size and verifies the pinned certificate before HTTP bytes.
It requires TLS 1.2 or newer; older router firmware may be incompatible.

## Isolation limits

Compose runs non-root with read-only filesystem, no capabilities, no published
ports, no host networking and no Docker socket. It limits CPU, memory and PIDs.
The code restricts its network destinations, but Compose does NOT impose an OS
egress firewall. A compromised dependency could bypass application guards.
For stronger assurance use a dedicated VM/VLAN and firewall permitting only
the router's TCP 443 destination for this workload. Do not change a shared host's
firewall blindly; existing services and Docker rules need individual review.

Dependencies have version/hash locks. The Python image tag is mutable, so record
the tested image digest for your deployment; verify updates before rebuilding.
We have not audited all Python, OpenSSL or cryptography source or binary wheels.

Report security problems privately to your deployment maintainer or the GitHub
repository's private vulnerability reporting channel, if enabled. Never post
credentials, real outputs or unrestricted diagnostic bundles in an issue.
