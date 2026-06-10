"""
ledger.py — a permissioned, single-writer, append-only, hash-chained ledger with a
genesis charter and a deterministic validator. Domain-agnostic; the per-domain charter
(YAML) supplies the block vocabulary, schema, hard invariants and soft rules.

Design (see Health Domain Charter):
  - GENESIS block (seq 0) carries the immutable charter.
  - Every later block links to the previous via prev_hash and carries its own sha256 hash
    over (prev_hash, timestamp, actor, block_type, canonical(payload), domain).
  - propose() runs the validator: HARD invariants -> reject; SOFT rules -> commit + flag /
    auto-append `warning` blocks. There is NO update/delete path (H2): corrections are
    `errata` blocks referencing a target block_id.
  - capture_raw() is the deterministic capture path — it commits a raw_entry verbatim,
    before any agent runs, so input is never lost to a flaky agent.
  - verify_chain() re-derives every hash to prove the ledger is untampered.

This is the first slice of the "Deterministic DBs" feature; structured + RAG tiers are
projections built by replaying the chain (not built here yet).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

GENESIS_PREV = "0" * 64
HERE = Path(__file__).resolve().parent


# ── hashing ────────────────────────────────────────────────────────────────────
def _canon(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def block_hash(prev_hash: str, ts: str, actor: str, block_type: str,
               payload: dict, domain: str) -> str:
    material = "|".join([prev_hash, ts, actor, block_type, _canon(payload), domain])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


# ── storage ────────────────────────────────────────────────────────────────────
def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS ledger ("
        " seq INTEGER PRIMARY KEY AUTOINCREMENT,"
        " block_id TEXT UNIQUE NOT NULL,"
        " domain TEXT NOT NULL,"
        " block_type TEXT NOT NULL,"
        " actor TEXT NOT NULL,"
        " timestamp TEXT NOT NULL,"
        " payload TEXT NOT NULL,"      # canonical JSON
        " ref TEXT,"                    # errata / warning target block_id
        " prev_hash TEXT NOT NULL,"
        " hash TEXT NOT NULL)")
    conn.commit()
    return conn


def _head(conn) -> Optional[tuple]:
    return conn.execute("SELECT seq, hash FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()


def _block_exists(conn, block_id: str) -> bool:
    return conn.execute("SELECT 1 FROM ledger WHERE block_id=?", (block_id,)).fetchone() is not None


def _has_prior_approval(conn) -> bool:
    return conn.execute("SELECT 1 FROM ledger WHERE block_type='approval' LIMIT 1").fetchone() is not None


def load_charter(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def get_charter(db_path: str) -> Optional[dict]:
    """The governing charter is the one COMMITTED in the genesis block — not the file
    (which could drift). Validation should use this, so the constitution is immutable."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT payload FROM ledger WHERE block_type='genesis' ORDER BY seq ASC LIMIT 1").fetchone()
        return json.loads(row[0])["charter"] if row else None
    finally:
        conn.close()


# ── init / genesis ───────────────────────────────────────────────────────────────
def init_ledger(db_path: str, charter: dict) -> dict:
    """Open the ledger; write the genesis block from the charter if empty."""
    conn = _connect(db_path)
    try:
        if _head(conn) is None:
            ts = datetime.now().isoformat(timespec="seconds")
            payload = {"charter": charter}
            h = block_hash(GENESIS_PREV, ts, "system", "genesis", payload, charter["domain"])
            bid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO ledger (block_id, domain, block_type, actor, timestamp, payload, ref, prev_hash, hash)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (bid, charter["domain"], "genesis", "system", ts, _canon(payload), None, GENESIS_PREV, h))
            conn.commit()
        return {"domain": charter["domain"], "height": _head(conn)[0]}
    finally:
        conn.close()


# ── the validator + commit ───────────────────────────────────────────────────────
def propose(db_path: str, actor: str, block_type: str, payload: dict,
            charter: dict, ref: Optional[str] = None) -> dict:
    """Validate a proposed block against the charter; commit or reject.

    Returns {committed: True, block, warnings:[...]} or {committed: False, rejected:[...]}.
    """
    conn = _connect(db_path)
    try:
        reasons = []
        # H4 provenance
        if not actor or not block_type:
            reasons.append("H4_provenance: missing actor or block_type")
        # H5 schema
        bt = charter.get("block_types", {}).get(block_type)
        if bt is None:
            reasons.append(f"H5_schema_valid: unknown block_type '{block_type}'")
        else:
            for f in bt.get("required", []):
                v = payload.get(f)
                if v is None or v == "" or v == []:
                    reasons.append(f"H5_schema_valid: missing required field '{f}' for {block_type}")
        # H3 raw completeness
        if block_type == "raw_entry" and not str(payload.get("text", "")).strip():
            reasons.append("H3_raw_complete: raw_entry text is empty")
        # H2 append-only — corrections must be errata referencing a real block
        if block_type == "errata" and not (ref and _block_exists(conn, ref)):
            reasons.append("H2_append_only: errata must reference an existing block_id")
        # H6 sovereignty — egress requires prior approval
        if block_type in (charter.get("egress_block_types") or []) and not _has_prior_approval(conn):
            reasons.append("H6_sovereignty: egress requires a prior approval block")

        if reasons:
            return {"committed": False, "rejected": reasons}

        block = _commit(conn, actor, block_type, payload, charter, ref)
        warnings = _run_soft_rules(conn, block, charter)
        return {"committed": True, "block": block, "warnings": warnings}
    finally:
        conn.close()


def _commit(conn, actor, block_type, payload, charter, ref=None) -> dict:
    prev = _head(conn)
    prev_hash = prev[1] if prev else GENESIS_PREV
    ts = datetime.now().isoformat(timespec="seconds")
    h = block_hash(prev_hash, ts, actor, block_type, payload, charter["domain"])
    bid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO ledger (block_id, domain, block_type, actor, timestamp, payload, ref, prev_hash, hash)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (bid, charter["domain"], block_type, actor, ts, _canon(payload), ref, prev_hash, h))
    conn.commit()
    seq = _head(conn)[0]
    return {"seq": seq, "block_id": bid, "block_type": block_type, "actor": actor,
            "timestamp": ts, "payload": payload, "ref": ref, "prev_hash": prev_hash, "hash": h}


def capture_raw(db_path: str, text: str, charter: dict, actor: str = "user") -> dict:
    """Deterministic capture: commit the verbatim input as a raw_entry BEFORE any agent.
    This is the determinism guarantee — input is never lost to agent tool-roulette."""
    return propose(db_path, actor, "raw_entry", {"text": text}, charter)


# ── soft rules (commit, then flag / auto-warn) ─────────────────────────────────────
def _run_soft_rules(conn, block, charter) -> list:
    warnings = []
    soft = charter.get("soft_rules", {})
    # S2 interaction watch — scan text-ish fields for known triggers; auto-append a warning.
    s2 = soft.get("S2_interaction_watch", {})
    triggers = s2.get("triggers", {})
    text = " ".join(str(v) for v in block["payload"].values()).lower()
    if block["block_type"] in ("raw_entry", "event", "intervention", "adherence", "fact"):
        for concern, terms in triggers.items():
            hit = next((t for t in terms if t.lower() in text), None)
            if hit:
                msg = f"'{hit}' may be relevant to {concern.replace('_', '/')} — flagged for review."
                w = _commit(conn, "system", "warning",
                            {"rule": "S2_interaction_watch", "message": msg, "trigger": hit,
                             "concern": concern},
                            charter, ref=block["block_id"])
                warnings.append(w["payload"])
    # S3 completeness — flag (not block) missing dose/timing/severity.
    flags = []
    if block["block_type"] == "adherence" and not block["payload"].get("at"):
        flags.append("S3_completeness: adherence has no timing ('at')")
    if block["block_type"] == "intervention" and not block["payload"].get("dose"):
        flags.append("S3_completeness: intervention has no dose")
    if block["block_type"] == "event" and not block["payload"].get("severity"):
        flags.append("S3_completeness: event has no severity")
    if flags:
        warnings.append({"rule": "S3_completeness", "flags": flags})
    return warnings


# ── audit ──────────────────────────────────────────────────────────────────────
def verify_chain(db_path: str) -> dict:
    """Re-derive every hash to prove the ledger is untampered + correctly linked."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT seq, domain, block_type, actor, timestamp, payload, prev_hash, hash"
            " FROM ledger ORDER BY seq ASC").fetchall()
        prev = GENESIS_PREV
        for (seq, domain, bt, actor, ts, payload_json, prev_hash, h) in rows:
            payload = json.loads(payload_json)
            if prev_hash != prev:
                return {"ok": False, "bad_seq": seq, "reason": "broken prev_hash link"}
            recomputed = block_hash(prev_hash, ts, actor, bt, payload, domain)
            if recomputed != h:
                return {"ok": False, "bad_seq": seq, "reason": "hash mismatch (tampered)"}
            prev = h
        return {"ok": True, "height": len(rows)}
    finally:
        conn.close()


def chain(db_path: str, limit: int = 50) -> list:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT seq, block_type, actor, timestamp, payload, ref, substr(hash,1,10)"
            " FROM ledger ORDER BY seq ASC LIMIT ?", (limit,)).fetchall()
        return [{"seq": s, "type": bt, "actor": a, "ts": ts,
                 "payload": json.loads(p), "ref": r, "hash10": h}
                for (s, bt, a, ts, p, r, h) in rows]
    finally:
        conn.close()
