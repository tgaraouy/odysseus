#!/usr/bin/env bash
# On-demand Helm SANDBOX stack — fully isolated from production.
#
# Separate Compose project (helm-sbx), separate host ports, and separate volumes,
# so sandbox data never touches production. Production keeps running as the default
# project on :7000; sandbox runs on :7001. Bring it up to test, down when done
# (a 12GB box can't comfortably run both heavy stacks + Ollama at once).
#
#   ./helm-sandbox.sh up        build + start sandbox (app -> http://localhost:7001)
#   ./helm-sandbox.sh seed      register the bridge MCP (run once after first up)
#   ./helm-sandbox.sh ps        status
#   ./helm-sandbox.sh logs [svc]
#   ./helm-sandbox.sh down      stop + remove containers (keep sandbox data)
#   ./helm-sandbox.sh reset     down + delete sandbox volumes (pristine next up)
set -euo pipefail
cd "$(dirname "$0")"
DC=(docker compose -p helm-sbx --env-file .env.sandbox)
cmd="${1:-}"; [ $# -gt 0 ] && shift || true
case "$cmd" in
  up)    "${DC[@]}" up -d --build "$@" ;;
  seed)  "${DC[@]}" exec odysseus python scripts/seed_bridge_mcp.py ;;
  ps)    "${DC[@]}" ps -a "$@" ;;
  logs)  "${DC[@]}" logs -f "$@" ;;
  down)  "${DC[@]}" down "$@" ;;
  reset) "${DC[@]}" down -v "$@"; rm -rf data-sbx logs-sbx 2>/dev/null; echo "wiped sandbox volumes + data-sbx/ logs-sbx/" ;;
  *) echo "usage: $0 {up|seed|ps|logs|down|reset} [args]"; exit 1 ;;
esac
