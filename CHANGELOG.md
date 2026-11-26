# Changelog

## Unreleased

- Mirror urllib's one-shot HTTPS request framing, including a terminal
  `Connection: close` header after the session cookie, for observed Deco
  interoperability. Preserve certificate pinning and read guards.
- Add two generated TLS-peer request-shape regressions and record bounded live
  client/traffic alias correlation. This is not a long-term reliability claim.

## v0.1.0-alpha

First experimental community release. The Python package and local Docker image
use version 0.1.0; the GitHub release is marked prerelease.

- Read-only mesh status, clients, DHCP reservations and traffic tools over stdio.
- SSH deployment to a Linux Docker host without exposing an MCP HTTP listener.
- Required router certificate pin, secret-file enrollment and HMAC aliases.
- Guarded SDK read endpoints, no environment proxies or HTTP redirects.
- Unprivileged, read-only Docker service with resource limits and locked deps.
- English/Spanish instructions, security model and synthetic offline CI tests.
- 27 tests passed in the target Python 3.14 image. A mixed X20 1.4.0/M5 1.9.5
  mesh passed physical login, mesh status and client listing.

Known limits: physical reservations remain unverified; traffic units/accuracy,
long-running stability and other models/firmwares need testing. Some firmware
returns node associations that cannot be mapped to MAC aliases. Tool output may
be sent to a cloud AI provider. Application network checks are not an OS egress
firewall. See SECURITY.md and docs/validation.md.
