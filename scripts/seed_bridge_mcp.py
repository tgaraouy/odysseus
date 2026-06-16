#!/usr/bin/env python3
"""Register the MyOwnHealth bridge as an MCP server, idempotently.

On the live Mac the bridge runs under launchd and the app reaches it at
http://host.docker.internal:8770/mcp. With the CONTAINERIZED bridge (the
`bridge` compose service, profile "bridge"), the app reaches it on the compose
network at http://bridge:8770/mcp instead. New installs have no MCP row yet, so
this seeds one so /health's agent tools work without hand-adding it in the UI.

Run it INSIDE the app container after the stack is up:

    docker compose exec odysseus python scripts/seed_bridge_mcp.py

Override the URL/name/id via env: HEALTH_MCP_URL, HEALTH_MCP_NAME, HEALTH_MCP_ID.
Re-running is safe: it updates the existing row's url/transport/enabled in place.
"""
from __future__ import annotations

import os
import sys

# Runnable as `python scripts/seed_bridge_mcp.py` from /app (the container WORKDIR).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import McpServer, SessionLocal  # noqa: E402

SERVER_ID = os.getenv("HEALTH_MCP_ID", "myownhealth")
SERVER_NAME = os.getenv("HEALTH_MCP_NAME", "MyOwnHealth")
SERVER_URL = os.getenv("HEALTH_MCP_URL", "http://bridge:8770/mcp")


def main() -> int:
    db = SessionLocal()
    try:
        row = db.query(McpServer).filter(McpServer.id == SERVER_ID).one_or_none()
        if row is None:
            db.add(McpServer(
                id=SERVER_ID, name=SERVER_NAME, transport="http",
                url=SERVER_URL, is_enabled=True,
            ))
            action = "created"
        else:
            row.name, row.transport, row.url, row.is_enabled = (
                SERVER_NAME, "http", SERVER_URL, True)
            action = "updated"
        db.commit()
    finally:
        db.close()
    print(f"MyOwnHealth bridge MCP server {action}: id={SERVER_ID} -> {SERVER_URL}")
    print("Restart the app (or reconnect in Settings -> MCP) to connect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
