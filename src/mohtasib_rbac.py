"""
mohtasib_rbac.py — the app side of Mohtasib RBAC.

Two jobs:
  1. INJECT the authenticated user's role into mcp__mohtasib__ tool calls,
     overriding anything the model supplied (the bridge enforces the matrix but
     can only trust a role that comes from the session).
  2. MANAGE the user→role store (data/mohtasib_roles.json) for the admin UI.

The store is server-side; the model has no write path to it. Unmapped users get
no role → the bridge denies everything (fail-closed).
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

try:
    from src.constants import DATA_DIR as _DATA_DIR
except Exception:
    _DATA_DIR = os.environ.get("DATA_DIR", "data")
_STORE = os.path.join(_DATA_DIR, "mohtasib_roles.json")
_MOHTASIB_PREFIX = "mcp__mohtasib__"

# The catalogue of assignable roles (mirrors the bridge's rbac.ROLES).
ROLE_CATALOG = [
    {"id": "verificateur", "label": "Vérificateur / Contrôleur",
     "desc": "Travaille les dossiers : capture, signalements, réconciliation. Propose, ne valide pas."},
    {"id": "chef_mission", "label": "Chef de mission",
     "desc": "Cadre le périmètre, affecte, revoit, approuve les livrables."},
    {"id": "magistrat", "label": "Magistrat rapporteur",
     "desc": "Autorité de validation : promeut un signalement en constat, signe."},
    {"id": "ethique", "label": "Responsable éthique",
     "desc": "Seul à lire le contenu DOP / conflits ; décide les suites."},
    {"id": "president", "label": "Président de chambre / CRC",
     "desc": "Pilotage : portefeuille, risque, couverture, contreseing."},
    {"id": "admin", "label": "Admin SI / DPO",
     "desc": "Rôles, souveraineté, intégrité du journal. Aucun accès au contenu d'audit."},
]
VALID_ROLES = {r["id"] for r in ROLE_CATALOG}


# ── store ────────────────────────────────────────────────────────────────────
def _read_store() -> dict:
    try:
        with open(_STORE, encoding="utf-8") as f:
            m = json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning(f"mohtasib_roles.json unreadable: {e}")
        return {}
    # drop the optional "_note" and any non-list values
    return {k: v for k, v in m.items() if not k.startswith("_") and isinstance(v, list)}


def _write_store(mapping: dict):
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp = _STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _STORE)


def list_assignments() -> dict:
    """{username: [roles]} for all users that have any Mohtasib role."""
    return _read_store()


def set_roles(user: str, roles) -> list:
    """Assign roles to a user (invalid roles are dropped; empty clears the user).
    Returns the stored roles. Admin-gated at the route."""
    if isinstance(roles, str):
        roles = [roles]
    roles = sorted({r for r in roles if r in VALID_ROLES})
    m = _read_store()
    if roles:
        m[user] = roles
    else:
        m.pop(user, None)
    _write_store(m)
    logger.info(f"mohtasib RBAC: set roles for {user!r} → {roles}")
    return m.get(user, [])


# ── injection (session role → bridge) ────────────────────────────────────────
def role_for_owner(owner):
    """Return the session user's Mohtasib role(s) as a comma-joined string
    (the bridge's rbac splits on commas). Empty = no role = deny-all."""
    if not owner:
        return ""
    return ",".join(_read_store().get(owner, []))


def inject_role(tool: str, args: dict, owner) -> dict:
    """For any mcp__mohtasib__ tool, force args['role'] to the session user's
    role — overriding whatever the model supplied. No-op for other tools."""
    if not tool.startswith(_MOHTASIB_PREFIX):
        return args
    args = dict(args or {})
    session_role = role_for_owner(owner)
    if args.get("role") not in (None, session_role):
        logger.info(f"mohtasib RBAC: overrode model-supplied role "
                    f"{args.get('role')!r} with session role {session_role!r} for {owner!r}")
    args["role"] = session_role
    return args
