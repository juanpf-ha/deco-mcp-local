# Validation record — 2026-11-25

Version: 0.1.0, experimental. Platform tested: Linux x86_64 with Docker Engine
and Compose, Python 3.14 inside the image.

## Automated checks

- 29 tests passed in the development test image with no external network, read-only root,
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

Physical DHCP reservation reads and traffic reads were subsequently exercised
through the actual stdio MCP process. Reservation counts, page limits,
next-offset handling and non-overlapping pages passed. Traffic output contained
online clients with finite non-negative rates, non-zero activity and descending
combined-rate ordering. Both tools returned pseudonymized data without raw
names, IP addresses or MAC addresses.

Repeated cross-tool validation was not fully successful: a later client read
failed, a follow-up client read succeeded, and follow-up traffic reads failed.
Safe stage diagnostics showed successful authentication followed by a 45-second
timeout waiting for the client-list response. The host also reported recent
PCIe/Wi-Fi hardware-link failures, and a subsequent SSH connection timed out.
Host connectivity is a plausible contributor, not a conclusively isolated cause.
The results do not establish sustained reliability or a complete cross-snapshot
alias-correlation pass. No retry loop or host/router configuration change was
used to conceal these failures.

A follow-up correlation attempt again failed on the client tool. During its
defined observation window, SSH remained usable and the kernel recorded no new
PCIe Link Down, missing-card or Wi-Fi transaction-failure events. Thus the
earlier hardware events do not by themselves explain every failed read. A
diagnostic read omitting the SDK's device selector also failed after successful
authentication; it was not adopted as a production change. Client-list API and
transport behavior still require isolation before claiming repeatable success.

## Explicit connection-close investigation

The router's own public client-list model confirmed the SDK's endpoint and
`device_mac: "default"` selector. A controlled alternating A/B experiment then
changed only the HTTPS request's `Connection` header, keeping credentials,
request body, TLS pin and read guards unchanged. Both original-header attempts
failed with connection resets; both explicit `Connection: close` attempts
succeeded. An earlier explicit-close client/traffic pair also completed with
matching address aliases for all overlapping devices.

The first installed change added the close header before the session cookie and
still failed the actual stdio check. The reference diagnostic appended it after
the cookie; repeating that exact request shape succeeded. The implementation
therefore preserves urllib's header order, with the session cookie preceding
the final explicit close header. This is an empirical interoperability
hypothesis, not a claim that HTTP generally requires that order or that the
firmware's internal failure mechanism has been established.

Two generated TLS-peer regressions preserve the chosen request shape. Each was
observed failing before its corresponding change and passing afterward; these
synthetic peers do not establish physical firmware causality.

After deployment, the actual unmodified stdio MCP client and traffic tools both
completed. All overlapping device aliases retained the same address aliases;
both outputs omitted names and raw IP/MAC addresses. The original deployment
image was retained for rollback. This closes the bounded cross-snapshot check,
but does not demonstrate prolonged stability or exclude unrelated host faults.

Traffic units and accuracy have not been independently validated. Persistent
operation, Wi-Fi fault recovery and sustained repeatability remain pending.
The successful bounded check should not be treated as certification for an
unattended monitoring service.

Certificate observation is not proof of identity. The deployment operator must
independently verify the certificate and enroll credentials locally before
querying a physical router. Public CI must continue using synthetic data only.
