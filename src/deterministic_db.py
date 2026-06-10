"""
deterministic_db.py — Odysseus integration for the Deterministic-DBs ledger.

Wires the hash-chained ledger (src/ledger.py) into Odysseus so a message in a domain
session (e.g. "🩺 Health Log") is captured VERBATIM onto the chain *before any agent
runs* — the determinism guarantee. The genesis charter is bootstrapped once from the
shipped charter file into a per-domain ledger DB in the data volume; thereafter the
committed charter governs.

Domains are matched by session name (first slice). The ledger lives in the Odysseus data
volume so it persists and stays self-contained ("only Odysseus").
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from src import ledger as L

logger = logging.getLogger(__name__)

# Repo root (this file is src/deterministic_db.py) → charters/ ships in the image.
_ROOT = Path(__file__).resolve().parent.parent
_CHARTER_DIR = _ROOT / "charters"
_LEDGER_DIR = Path(os.getenv("LEDGER_DIR", _ROOT / "data" / "ledger"))

# Domain registry: session-name match → (domain, charter file). Extend per domain.
_DOMAINS = [
    ("health", "🩺 health log", "health.charter.yaml"),
]


def _ledger_db(domain: str) -> str:
    return str(_LEDGER_DIR / f"{domain}.ledger.db")


def _ensure_genesis(domain: str, charter_file: str) -> dict:
    """Open the domain ledger; write genesis from the shipped charter if empty.
    Returns the governing (committed) charter."""
    db = _ledger_db(domain)
    if L.get_charter(db) is None:
        charter = L.load_charter(_CHARTER_DIR / charter_file)
        L.init_ledger(db, charter)
        logger.info(f"[ledger] genesis written for domain '{domain}' at {db}")
    return L.get_charter(db)


def _match_domain(session_name: str) -> tuple | None:
    name = (session_name or "").lower()
    for domain, needle, charter_file in _DOMAINS:
        if needle in name:
            return domain, charter_file
    return None


def capture_message(session_name: str, text: str, actor: str = "user") -> dict | None:
    """Deterministically capture a message onto the domain ledger if the session belongs
    to a registered domain. Returns the capture result, or None if not a domain session.
    Never raises into the chat path — callers should still guard, but this is defensive."""
    if not (text and text.strip()):
        return None
    match = _match_domain(session_name)
    if not match:
        return None
    domain, charter_file = match
    try:
        charter = _ensure_genesis(domain, charter_file)
        db = _ledger_db(domain)
        res = L.capture_raw(db, text.strip(), charter, actor=actor)
        if res.get("committed"):
            b = res["block"]
            logger.info(f"[ledger:{domain}] captured raw_entry seq={b['seq']} hash={b['hash'][:10]}")
        return res
    except Exception as e:
        logger.warning(f"[ledger:{domain}] capture failed: {type(e).__name__}: {e}")
        return {"committed": False, "error": str(e)}
