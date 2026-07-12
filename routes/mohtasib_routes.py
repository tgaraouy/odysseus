"""
mohtasib_routes.py — admin UI + API for Mohtasib role assignment.

  GET  /mohtasib/roles          → the admin page (logged-in users; the API gates)
  GET  /api/mohtasib/roles      → users × roles + the role catalogue (admin only)
  POST /api/mohtasib/roles      → assign roles to a user (admin only)

Role assignment is an admin task — the model has no path here. Every change is
logged. The store is data/mohtasib_roles.json, read by the injection layer.
"""
import os
import sys
import json
import logging
from collections import Counter
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.middleware import require_admin
from src.auth_helpers import require_user
from src.mohtasib_rbac import ROLE_CATALOG, list_assignments, set_roles, role_for_owner

logger = logging.getLogger(__name__)
_STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
_PAGE = os.path.join(_STATIC, "mohtasib-roles.html")
_CONSOLE = os.path.join(_STATIC, "mohtasib-console.html")

# The live procurement data, mounted read-only from the prototype.
_DATA = "/app/mohtasib-data"
_SECTIONS = ("dashboard", "capture", "signalements", "reconciliation", "validation",
             "ethique", "livrables", "journal", "metriques", "admin")
_ACTIONS = ("view", "act", "validate", "admin")


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _rbac_matrix():
    """Load the bridge's matrix from the mounted prototype (single source)."""
    try:
        if os.path.join(_DATA, "agentic") not in sys.path:
            sys.path.insert(0, os.path.join(_DATA, "agentic"))
        import rbac  # from the mounted prototype
        return rbac
    except Exception:
        return None


def _read_journal_ro(db):
    """Read + verify the hash chain WITHOUT writing (the mount is read-only, so
    journal.verifier()'s CREATE TABLE would fail). Uses journal._hash to re-derive."""
    import sqlite3
    from collections import Counter
    if not os.path.exists(db):
        return {"hauteur": 0, "verifiee": True, "par_type": {}, "recents": []}
    if _DATA not in sys.path:
        sys.path.insert(0, _DATA)
    import journal as J
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT seq, block_type, actor, timestamp, payload, confidence, "
                           "prev_hash, hash FROM journal ORDER BY seq ASC").fetchall()
    finally:
        con.close()
    prev = "0" * 64
    ok = True
    for (seq, bt, actor, ts, pj, conf, ph, h) in rows:
        if ph != prev or J._hash(ph, ts, actor, bt, json.loads(pj), conf) != h:
            ok = False
            break
        prev = h
    types = Counter(r[1] for r in rows)
    recents = [{"type": r[1], "actor": r[2], "ts": r[3], "confiance": r[5], "hash10": r[7][:10]}
               for r in rows[-8:][::-1]]
    return {"hauteur": len(rows), "verifiee": ok, "par_type": dict(types), "recents": recents}


def _access_for(roles_csv):
    """{section: [allowed actions]} for the caller — drives which sections show."""
    rbac = _rbac_matrix()
    if not rbac:
        return {}
    out = {}
    for s in _SECTIONS:
        acts = [a for a in _ACTIONS if rbac.can_any(roles_csv, s, a)]
        if not acts and rbac.can_any(roles_csv, s, "exists"):
            acts = ["exists"]
        out[s] = acts
    return out


class RoleAssignment(BaseModel):
    username: str
    roles: list[str] = []


def setup_mohtasib_routes(auth_manager):
    router = APIRouter()

    @router.get("/mohtasib/roles")
    def roles_page():
        # The page itself is static; the API below enforces admin. The app's
        # auth middleware already redirects anonymous users to /login.
        return FileResponse(_PAGE)

    @router.get("/api/mohtasib/roles")
    def api_list(_admin: str = Depends(require_admin)):
        assigned = list_assignments()
        users = []
        for username, u in sorted((auth_manager.users or {}).items()):
            users.append({
                "username": username,
                "is_admin": bool(u.get("is_admin")),
                "roles": assigned.get(username, []),
            })
        # include any assigned username not present in auth.users (stale/manual)
        for username, roles in assigned.items():
            if username not in (auth_manager.users or {}):
                users.append({"username": username, "is_admin": False,
                              "roles": roles, "orphan": True})
        return {"users": users, "catalog": ROLE_CATALOG}

    @router.post("/api/mohtasib/roles")
    def api_set(payload: RoleAssignment, _admin: str = Depends(require_admin)):
        if not payload.username:
            raise HTTPException(400, "username requis")
        stored = set_roles(payload.username, payload.roles)
        logger.info(f"mohtasib role assignment: {payload.username} → {stored} (by admin)")
        return {"username": payload.username, "roles": stored}

    # ── the domain console: the Mohtasib sections + data/analysis ────────────
    @router.get("/mohtasib")
    def console_page():
        return FileResponse(_CONSOLE)

    @router.get("/api/mohtasib/overview")
    def api_overview(user: str = Depends(require_user)):
        roles_csv = role_for_owner(user)
        access = _access_for(roles_csv)

        def visible(section, action="view"):
            return action in access.get(section, [])

        flags = _read_json(os.path.join(_DATA, "flags.json"), [])
        metrics = _read_json(os.path.join(_DATA, "metrics.json"), {})

        # dashboard aggregates (always computed; shown if dashboard access)
        sev = Counter(f.get("severite") for f in flags)
        tenders = sorted({f.get("tender") for f in flags})
        pending = [f for f in flags if f.get("statut") != "valide"]
        dashboard = {
            "n_tenders": len(tenders),
            "n_signalements": len(flags),
            "par_severite": {k: sev.get(k, 0) for k in ("critique", "majeur", "mineur")},
            "en_attente_validation": len(pending),
        }

        # signalements — full content only with view; else masked count
        if visible("signalements"):
            signalements = flags
        elif "exists" in access.get("signalements", []):
            signalements = {"masque": True, "n": len(flags)}
        else:
            signalements = None

        # ethics/DOP — content only for ethique; existence for restricted; none else
        dop = [f for f in flags if f.get("controle") == "C-DOP"
               or "probité" in (f.get("titre", "") + f.get("controle", "")).lower()]
        if visible("ethique"):
            ethique = dop
        elif "exists" in access.get("ethique", []):
            ethique = {"masque": True, "n": len(dop)}
        else:
            ethique = None

        # validation queue — the pending items; magistrat can validate
        validation = {"file": pending, "peut_valider": visible("validation", "validate")} \
            if visible("validation") or "exists" in access.get("validation", []) else None

        # journal — read the mounted hash chain (read-only, verified in place)
        journal_info = None
        if visible("journal"):
            try:
                journal_info = _read_journal_ro(os.path.join(_DATA, "data", "journal.db"))
            except Exception as e:
                journal_info = {"erreur": str(e)}

        return {
            "user": user, "roles": roles_csv.split(",") if roles_csv else [],
            "access": access,
            "dashboard": dashboard if visible("dashboard") or "exists" in access.get("dashboard", []) else None,
            "signalements": signalements,
            "ethique": ethique,
            "validation": validation,
            "metriques": metrics if visible("metriques") else None,
            "journal": journal_info,
        }

    return router
