"""
mohtasib_routes.py — admin UI + API for Mohtasib role assignment.

  GET  /mohtasib/roles          → the admin page (logged-in users; the API gates)
  GET  /api/mohtasib/roles      → users × roles + the role catalogue (admin only)
  POST /api/mohtasib/roles      → assign roles to a user (admin only)

Role assignment is an admin task — the model has no path here. Every change is
logged. The store is data/mohtasib_roles.json, read by the injection layer.
"""
import os
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.middleware import require_admin
from src.mohtasib_rbac import ROLE_CATALOG, list_assignments, set_roles

logger = logging.getLogger(__name__)
_PAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "static", "mohtasib-roles.html")


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

    return router
