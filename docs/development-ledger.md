# Development record

- Implemented in an independent repository on `feat/private-stdio`; no shared
  source branch or existing service configuration was changed.
- Ruling: the user's instruction to start authorizes the already discussed
  read-only Wyse approach. Use the existing reviewed SDK with a new small stdio
  layer rather than retaining the upstream HTTP server and write tools.
- Initial tests failed because implementation modules did not exist. After
  implementation, 19 offline tests passed on Python 3.12. A further actual-SDK
  integration test requires Python 3.14 and is run in Docker, not claimed from
  the Python 3.12 run.
- Independent security reviewer inspected code, Compose and SDK integration
  before the deployment build. No important findings; real-device compatibility
  remains unverified. Follow-up review includes final docs/integration tests.
- Runtime destination checks are application-level; no host firewall changes
  were made. This limitation is explicit in SECURITY.md.
- Working tree and first Git commit were scanned for known private environment
  identifiers; none found. Secret paths are ignored and excluded from Docker.
- Independent review found a race in the TLS test peer (unread POST body before
  closing). Fixed the peer and added a fragmented-request regression.
- Regression: SDK ValueError was classified as a user argument error. Observed
  failing test, introduced ArgumentError for client validation, suite green.
- Target Docker tests initially failed because read-only tests had no writable
  temp directory. Added a test-only RAM `/tmp` mount to documented/CI commands.
  Production Compose still needs no writable mount.
- Final target run: all 26 tests passed on Python 3.14, including the actual SDK
  encrypted handshake, in an offline non-root read-only container with 128 MB
  limit. Runtime image built and `--version` returned 0.1.0.
- Compose smoke with disposable synthetic enrollment passed initialize, tools
  catalog, write rejection, file-secret mounts and EOF cleanup. Its temporary
  project was torn down. No physical-router login was attempted.
- Runtime certificate inspection succeeded and matched a separate OpenSSL
  observation. This verifies reachability, not independent identity enrollment.
- Final independent reviewer found no remaining important issues. Known private
  environment identifiers absent from all Git commits checked.
