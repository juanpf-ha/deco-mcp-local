# Local Deco MCP: design

Build a community-usable, privacy-first, read-only MCP for an existing Linux
Docker host. Inspired by nitin23c/deco-mcp at 7fec80f and using
roquerodrigo/tplink-deco-api 2.1.1. Preserve MIT attribution.

## Decisions

- Run the MCP over newline-delimited stdio, optionally through SSH. No HTTP
  listener, bearer token, telemetry, update checker or cloud API.
- Four tools: mesh status, paginated clients, paginated reservations and traffic.
  No write tools, generic requests, raw configuration, Wi-Fi passwords or SSIDs.
- Use explicit output field allowlists. Names and addresses become HMAC aliases
  by default; model, firmware and topology are still potentially identifying.
  This is pseudonymization, not irreversible anonymization.
- Explicit local operator setting may enable device names/IP/MAC for diagnosis.
  A tool argument cannot change the privacy mode.
- Password and independent alias key from mounted files; no secret CLI arguments.
- Require a SHA-256 pin of the router certificate. Verify before sending any HTTP
  request bytes. Certificate inspection makes no login and must be verified by
  the operator using a trusted path before enrollment.
- Router address must be RFC1918 IPv4. Custom HTTPS transport uses no environment
  proxies and follows no redirects; cap responses and enforce operation allowlist.
- Dependency locked with hashes; Docker runs nonroot, read-only, without host
  networking, Docker socket, privileged mode or published ports.
- Do not modify existing host firewall or home automation services automatically.
  Document that runtime destination restrictions in code are not an OS firewall.
- Secrets and real observations stay outside the public repository and Git history.

## Alternatives

Forking the original HTTP server is quicker but retains an unnecessary network
listener. Rewriting the Deco authentication protocol increases risk and effort.
Chosen: a small new stdio layer around the reviewed SDK, adapting upstream read
tool ideas with attribution, retaining its pinned dependency lock.

## Validation and limits

Test config rejection, secret handling, pseudonymization, pagination, protocol
errors, write rejection, TLS pin mismatch before HTTP, no redirect/proxy use,
output allowlists and malicious device names using synthetic fixtures. Build and
smoke-test Docker on the target host before real router access. Real-device login
needs locally enrolled credentials and certificate pin; compatibility is unknown
until that succeeds. Existing Wi-Fi instability can interrupt SSH.

Public docs must never claim zero cloud processing: tool output reaches the MCP
client and may be sent to its model provider. GitHub publication is a separate
step after reviewing the actual repository and selecting a destination.
