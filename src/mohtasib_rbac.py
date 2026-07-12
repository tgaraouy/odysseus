"""
mohtasib_rbac.py — inject the AUTHENTICATED user's Mohtasib role into calls to
the mohtasib MCP bridge.

The bridge enforces the role × section matrix, but it can only trust the role if
that role comes from the session, not the model. This module resolves the
logged-in user (`owner`) to their assigned Mohtasib role(s) from a server-side
store the model cannot touch, and OVERWRITES any role the model tried to supply.

Store: data/mohtasib_roles.json — {"<app-username>": ["magistrat", ...]}.
Managed by an admin (the model has no write path to it). Unmapped users get NO
role → the bridge denies everything (fail-closed).
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


def role_for_owner(owner):
    """Return the session user's Mohtasib role(s) as a comma-joined string
    (the bridge's rbac splits on commas). Empty string = no role = deny-all."""
    if not owner:
        return ""
    try:
        with open(_STORE, encoding="utf-8") as f:
            mapping = json.load(f)
    except FileNotFoundError:
        return ""
    except Exception as e:
        logger.warning(f"mohtasib_roles.json unreadable: {e}")
        return ""
    roles = mapping.get(owner) or []
    if isinstance(roles, str):
        roles = [roles]
    return ",".join(r for r in roles if r)


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
