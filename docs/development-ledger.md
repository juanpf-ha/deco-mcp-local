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
