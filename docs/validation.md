# Validation record — 2026-11-25

Version: 0.1.0, experimental. Platform tested: Linux x86_64 with Docker Engine
and Compose, Python 3.14 inside the image.

## Automated checks

- 27 tests passed in the latest test image with no external network, read-only root,
  test-only `/tmp` RAM mount, unprivileged UID, capabilities dropped and 128 MB
  memory limit. No tests skipped on the target Python 3.14 runtime.
- Includes the pinned SDK's RSA/AES login and read calls against synthetic
  encrypted responses, plus rejection of an attempted write.
- TLS tests cover real generated certificates/sockets, pin mismatch before HTTP,
  no proxy use, redirect rejection, bounds and fragmented test-peer requests.
- CLI subprocess tests cover clean stdio, secret-file loading, protocol/catalog
  output, no credential logs and write rejection before a router call.
- Separate Compose smoke used disposable synthetic credentials, started the
  service on demand, exchanged MCP messages and removed the temporary project.
- Runtime image builds and reports version 0.1.0. Certificate-only inspection
  reaches a local HTTPS router without sending HTTP/login credentials.
- Independent code/security review completed; reported test-peer race fixed.
- Known private-environment identifier scan found no matches in checked Git
  history. No real configuration, passwords, keys or router output is tracked.

## Physical-device observations and remaining limits

Physical authentication, mesh status and client-list reads have subsequently
succeeded on an X20 1.4.0 gateway with M5 1.9.5 satellites. The client-list read
exceeded the original 10-second operation timeout and succeeded with 45 seconds;
the default is now 45 and configurable within 1–60 seconds. Actual identifying
output remains outside the repository. This is a single deployment observation,
not certification across hardware revisions or firmware variants.

Reservations, persistent operation and Wi-Fi fault recovery remain unverified.
Traffic fields were present in the client-list response, but their units and
accuracy have not been independently validated.

Certificate observation is not proof of identity. The deployment operator must
independently verify the certificate and enroll credentials locally before
querying a physical router. Public CI must continue using synthetic data only.
