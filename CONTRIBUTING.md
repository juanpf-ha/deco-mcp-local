# Contributing

Use synthetic devices, names, addresses, certificate keys and passwords in tests.
Never commit .env, secrets/, SSH keys, real router responses, hostnames, screenshots
or production logs. Redacting a later commit does not remove previous history.

Tests: `python -m unittest discover -s tests -v` (Python 3.14 and locked deps).
Docker: build target `test`, then run it with `--network none --read-only` and
`--tmpfs /tmp:rw,noexec,nosuid,size=32m,mode=1777` for generated test certificates.
Add a failing regression test before changing a security boundary.

Changes to the pinned SDK or transport need a data-flow review and the real SDK
integration test. Do not add write endpoints, raw passthrough or a privacy tool
argument without revisiting the threat model. Do not run public CI against a
physical router or supply real credentials as CI secrets.

Before publishing, scan both working tree and complete Git history for secrets
and identifying data. The included synthetic fixtures are deliberately public.
