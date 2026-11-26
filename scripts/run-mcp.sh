#!/bin/sh
# Point an MCP stdio client at: ssh -T your-host /path/to/scripts/run-mcp.sh
# No pseudo-terminal: stdout must contain only MCP JSON-RPC.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec docker compose run --rm -T --no-deps deco-mcp
