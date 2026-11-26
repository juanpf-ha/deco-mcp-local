# Local Deco MCP implementation plan

Goal: deliver a read-only stdio MCP with a hardened Docker deployment and no
private environment data in the repository. Spec: design.md.

Architecture: configuration and aliases, a guarded SDK/HTTPS boundary, four
allowlisted query tools, a bounded stdio JSON-RPC dispatcher, generic deployment.
Stack: Python 3.14 runtime, stdlib unittest, pinned tplink-deco-api 2.1.1.

## Review focus

1. A fake TLS peer must receive zero HTTP bytes on a pin mismatch.
2. Device names, exceptions and unrecognized response fields must not leak secrets.
3. Requests to an unexpected address/path/operation must fail before network IO.
4. Oversized or malformed stdio messages must not corrupt subsequent responses.
5. Docker/SSH examples must keep secrets and real addresses out of Git and stdout.

## Tasks

- [ ] Tests first: Config.from_env, Privacy.device/address, QueryService.call,
  App.handle/serve, PinnedTransport and GuardedClient, using fictitious devices.
  Run unittest discovery and observe failure before implementation.
- [ ] Implement config.py, privacy.py, transport.py, router.py, tools.py,
  server.py and __main__.py. Run the complete test suite and fix failures.
- [ ] Add Dockerfile, compose.yaml, hashed requirements.lock, SSH examples,
  SECURITY, CONTRIBUTING, MIT attribution, English/Spanish usage docs and CI.
- [ ] Build/test isolated container on target; capture only generic outcomes in
  repo. Scan tracked files/history for private values. Independent code review.
- [ ] Deliver local Git branch and reproducible source archive. Real router
  enrollment and GitHub publication only with the missing local credentials and
  selected GitHub destination respectively.
