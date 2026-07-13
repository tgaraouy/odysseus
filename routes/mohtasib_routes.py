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


def _enrich_citations(flags):
    """Attach each control's Decree 2-22-431 citation (from the mounted registry)."""
    try:
        if _DATA not in sys.path:
            sys.path.insert(0, _DATA)
        import citations as CIT
        for f in flags:
            f["citation"] = CIT.citer(f.get("controle", ""))
    except Exception:
        pass
    return flags


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


# ── per-tender dossier assembly (real artifacts from the mounted prototype) ──
def _portal_index():
    """Map every portal.json in data/ by its 'reference' AND its file stem, so a
    signalement's tender label resolves to its extracted metadata + amendments."""
    idx = {}
    ddir = os.path.join(_DATA, "data")
    try:
        names = os.listdir(ddir)
    except Exception:
        return idx
    for fn in names:
        if not fn.endswith("_portal.json"):
            continue
        p = _read_json(os.path.join(ddir, fn), None)
        if not isinstance(p, dict):
            continue
        stem = fn[:-len("_portal.json")]
        idx[stem] = p
        ref = p.get("reference")
        if ref:
            idx[ref] = p
    return idx


def _find_capture(slug):
    """capture.json carries the OCR fidelity evidence for a tender's source PDF.
    It lives under inbox/captured_<slug>/ in the prototype; return {} if absent."""
    for cand in (os.path.join(_DATA, "inbox", "captured_" + slug, "capture.json"),
                 os.path.join(_DATA, "data", "captured", slug, "capture.json")):
        c = _read_json(cand, None)
        if isinstance(c, dict):
            return c
    return {}


def _journal_for_tender(ref):
    """Return the journal blocks (validation, capture, livrable) that name this
    tender — read-only, no writes to the mount."""
    import sqlite3
    db = os.path.join(_DATA, "data", "journal.db")
    if not os.path.exists(db):
        return []
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT seq, block_type, actor, timestamp, payload, confidence, hash "
                           "FROM journal ORDER BY seq ASC").fetchall()
    except Exception:
        return []
    finally:
        con.close()
    import re
    # take the "AO<number>" head, stopping at the year separator: AO-12/2024 -> AO12
    m = re.match(r"([A-Za-z]+)[-_ ]?(\d+)", ref)
    token = (m.group(1) + m.group(2)).upper() if m else re.sub(r"[^A-Z0-9]", "", ref.upper())[:4]
    out = []
    for (seq, bt, actor, ts, pj, conf, h) in rows:
        try:
            p = json.loads(pj)
        except Exception:
            p = {}
        blob = re.sub(r"[^A-Z0-9]", "", json.dumps(p, ensure_ascii=False).upper())
        if token and token in blob:
            out.append({"seq": seq, "type": bt, "actor": actor, "ts": ts,
                        "confiance": conf, "hash10": (h or "")[:10],
                        "verdict": p.get("verdict"), "claim_id": p.get("claim_id")})
    return out


def _tender_capture_fidelite(cap):
    """Derive an honest fidelity read from capture.json (no invented numbers)."""
    if not cap:
        return None
    tl, ocr = cap.get("text_layer_chars"), cap.get("ocr_chars")
    recall = None
    if isinstance(tl, int) and isinstance(ocr, int) and max(tl, ocr):
        recall = round(min(tl, ocr) / max(tl, ocr), 3)
    return {
        "pdf": cap.get("pdf"), "pages": cap.get("pages"),
        "source_retenue": cap.get("kept"), "langue_ocr": cap.get("ocr_lang"),
        "text_layer_chars": tl, "ocr_chars": ocr,
        "text_layer_sain": cap.get("text_layer_sane"),
        "concordance_tl_ocr": recall,
        "erreur_ocr": cap.get("ocr_error"),
    }


def _build_dossier(ref, flags, access, livrables):
    """Assemble the full end-to-end chain for one tender from real artifacts.
    Each stage is present with data, or explicitly marked absent — never faked."""
    def can(section, action="view"):
        return action in access.get(section, [])

    slug = ref.replace("/", "_").replace(" ", "_")
    portal = _portal_index().get(ref) or _portal_index().get(slug)
    cap = _find_capture(slug) if slug else {}
    tflags = [f for f in flags if f.get("tender") == ref]
    sev = Counter(f.get("severite") for f in tflags)

    # 1. Collecte — source + extracted metadata
    if portal:
        docs = list(portal.get("documents_presents", []))
        amend = portal.get("amendements", [])
        collecte = {
            "present": True,
            "reference": portal.get("reference", ref),
            "objet": portal.get("objet"),
            "procedure": portal.get("procedure"),
            "montant_estime_dh": portal.get("montant_estime_dh"),
            "date_publication": portal.get("date_publication"),
            "date_ouverture": portal.get("date_ouverture"),
            "documents_presents": docs,
            "sha256_pdf": portal.get("sha256_pdf"),
            "n_versions": 1 + len(amend),
        }
    else:
        collecte = {"present": False,
                    "note": "Aucun portal.json extrait pour ce marché — signalé mais dossier "
                            "source non ingéré dans ce périmètre."}

    # 2. Capture / OCR fidelity
    capture = _tender_capture_fidelite(cap)

    # 3. Extraction — the base (avant amendements) vs courant
    extraction = None
    if portal:
        base = portal.get("base_origine", {})
        extraction = {
            "base": {k: base.get(k) for k in ("objet", "date_ouverture", "montant_estime_dh")},
            "courant": {"objet": portal.get("objet"), "date_ouverture": portal.get("date_ouverture"),
                        "montant_estime_dh": portal.get("montant_estime_dh")},
        }

    # 4. Réconciliation — the amendment chain (no blind last-writer-wins)
    reconciliation = None
    if portal and portal.get("amendements"):
        chain = []
        for a in portal["amendements"]:
            champs = []
            for field, ch in (a.get("champs_modifies") or {}).items():
                champs.append({"champ": field, "avant": ch.get("avant"), "apres": ch.get("apres"),
                               "statut": ch.get("statut"), "problemes": ch.get("problemes", [])})
            chain.append({"document": a.get("document"), "date": a.get("date_document"),
                          "type": a.get("type"), "sha256": a.get("sha256"), "champs": champs})
        reconciliation = {"versions": chain}

    # 5. Contrôles — signalements (RBAC: content vs masked count)
    if can("signalements"):
        controles = tflags
    elif "exists" in access.get("signalements", []):
        controles = {"masque": True, "n": len(tflags)}
    else:
        controles = None

    # 6. Validation — journal verdicts + pending
    validation = None
    if can("validation") or "exists" in access.get("validation", []):
        jval = [b for b in _journal_for_tender(ref) if b["type"] == "validation"]
        pend = [f for f in tflags if f.get("statut") != "valide"]
        validation = {"verdicts": jval, "en_attente": len(pend),
                      "peut_valider": can("validation", "validate")}

    # 7. Livrables — the deliverables that cite this tender
    livr = None
    if can("livrables"):
        livr = [l for l in livrables if ref in l.get("cite", []) or l.get("global")]

    # 8. Journal — the tender's hash-chained proof blocks
    jour = None
    if can("journal"):
        jour = _journal_for_tender(ref)

    return {
        "reference": ref,
        "par_severite": {k: sev.get(k, 0) for k in ("critique", "majeur", "mineur")},
        "n_signalements": len(tflags),
        "collecte": collecte,
        "capture": capture,
        "extraction": extraction,
        "reconciliation": reconciliation,
        "controles": controles,
        "validation": validation,
        "livrables": livr,
        "journal": jour,
    }


def _livrables_index():
    """The generated deliverables in livrables/, with which tenders each cites."""
    ldir = os.path.join(_DATA, "livrables")
    out = []
    try:
        names = sorted(os.listdir(ldir))
    except Exception:
        return out
    for fn in names:
        if not fn.endswith(".md"):
            continue
        try:
            with open(os.path.join(ldir, fn), encoding="utf-8") as f:
                body = f.read()
        except Exception:
            body = ""
        cite = [t for t in ("AO-12/2024", "AO_07_2024_essaouira", "AO_15_2024_ar_scanne")
                if t in body or t.replace("_", " ") in body or t.split("/")[0] in body]
        out.append({"fichier": fn, "titre": body.splitlines()[0].lstrip("# ").strip() if body else fn,
                    "octets": len(body.encode("utf-8")), "cite": cite, "global": not cite})
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
        _enrich_citations(flags)  # attach the Decree 2-22-431 citation to each alert
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

        # dossiers — one row per tender, so the console can list them and drill in
        dossiers = None
        if visible("dashboard") or visible("signalements") or "exists" in access.get("signalements", []):
            pidx = _portal_index()
            dossiers = []
            for t in tenders:
                tf = [f for f in flags if f.get("tender") == t]
                sv = Counter(f.get("severite") for f in tf)
                slug = t.replace("/", "_").replace(" ", "_")
                dossiers.append({
                    "reference": t,
                    "n_signalements": len(tf),
                    "par_severite": {k: sv.get(k, 0) for k in ("critique", "majeur", "mineur")},
                    "has_portal": bool(pidx.get(t) or pidx.get(slug)),
                    "has_capture": bool(_find_capture(slug)),
                    "en_attente": len([f for f in tf if f.get("statut") != "valide"]),
                })

        # schémas inter-marchés — the predictive collusion detector, run live on
        # real attribution data (visible with signalement/dashboard access)
        inter_marche = None
        if visible("signalements") or visible("dashboard"):
            try:
                import importlib
                if _DATA not in sys.path:
                    sys.path.insert(0, _DATA)
                import collusion as COL
                importlib.reload(COL)
                _cd, _recs, _label = COL.load()
                inter_marche = COL.detect(_cd, _recs, _label)
                # attach deterministic PDF-metadata forensics + fractionnement (pre-computed)
                inter_marche["forensics"] = _read_json(os.path.join(_DATA, "forensics.json"), None)
                inter_marche["fractionnement"] = _read_json(os.path.join(_DATA, "fractionnement.json"), None)
                # citation per inter-marché + fractionnement signal
                try:
                    import citations as CIT
                    for s in inter_marche.get("signaux", []):
                        s["citation"] = CIT.citer(s.get("type", ""))
                    fr = inter_marche.get("fractionnement") or {}
                    for s in fr.get("signaux", []):
                        s["citation"] = CIT.citer(s.get("type", ""))
                except Exception:
                    pass
            except Exception as e:
                inter_marche = {"erreur": str(e)}

        # conformité au défi — the spec_conformance validator, run live (meta-assurance)
        conformite = None
        if visible("dashboard") or visible("metriques"):
            try:
                import importlib
                if _DATA not in sys.path:
                    sys.path.insert(0, _DATA)
                import spec_conformance as SC
                importlib.reload(SC)  # re-read flags/metrics/livrables on each call
                res = SC.build()
                conformite = {"resultats": res, "n": len(res),
                              "resume": dict(Counter(r["status"] for r in res))}
            except Exception as e:
                conformite = {"erreur": str(e)}

        return {
            "user": user, "roles": roles_csv.split(",") if roles_csv else [],
            "access": access,
            "dashboard": dashboard if visible("dashboard") or "exists" in access.get("dashboard", []) else None,
            "dossiers": dossiers,
            "signalements": signalements,
            "inter_marche": inter_marche,
            "ethique": ethique,
            "validation": validation,
            "metriques": metrics if visible("metriques") else None,
            "journal": journal_info,
            "conformite": conformite,
        }

    @router.get("/api/mohtasib/tender/{ref:path}")
    def api_tender(ref: str, user: str = Depends(require_user)):
        roles_csv = role_for_owner(user)
        access = _access_for(roles_csv)
        # gate: need at least dashboard or signalements existence to open a dossier
        if not (access.get("dashboard") or access.get("signalements")):
            raise HTTPException(403, "Accès refusé à ce dossier pour votre rôle.")
        flags = _read_json(os.path.join(_DATA, "flags.json"), [])
        _enrich_citations(flags)
        known = {f.get("tender") for f in flags}
        if ref not in known:
            raise HTTPException(404, f"Marché inconnu: {ref}")
        livrables = _livrables_index()
        return _build_dossier(ref, flags, access, livrables)

    @router.get("/api/mohtasib/livrable/{fichier}")
    def api_livrable(fichier: str, user: str = Depends(require_user)):
        roles_csv = role_for_owner(user)
        access = _access_for(roles_csv)
        if "view" not in access.get("livrables", []):
            raise HTTPException(403, "Accès refusé aux livrables pour votre rôle.")
        # whitelist against the index — never trust the path (blocks traversal)
        idx = {l["fichier"]: l for l in _livrables_index()}
        if fichier not in idx:
            raise HTTPException(404, f"Livrable inconnu: {fichier}")
        try:
            with open(os.path.join(_DATA, "livrables", fichier), encoding="utf-8") as f:
                md = f.read()
        except Exception as e:
            raise HTTPException(500, str(e))
        docx = fichier[:-3] + ".docx" if fichier.endswith(".md") else fichier + ".docx"
        has_docx = os.path.exists(os.path.join(_DATA, "livrables", docx))
        return {"fichier": fichier, "titre": idx[fichier].get("titre"), "markdown": md,
                "docx": docx if has_docx else None}

    @router.get("/api/mohtasib/livrable-docx/{fichier}")
    def api_livrable_docx(fichier: str, user: str = Depends(require_user)):
        roles_csv = role_for_owner(user)
        access = _access_for(roles_csv)
        if "view" not in access.get("livrables", []):
            raise HTTPException(403, "Accès refusé aux livrables pour votre rôle.")
        # only .docx whose .md is a known livrable (blocks traversal + arbitrary files)
        if not fichier.endswith(".docx"):
            raise HTTPException(404, "Format attendu: .docx")
        known_md = {l["fichier"] for l in _livrables_index()}
        if (fichier[:-5] + ".md") not in known_md:
            raise HTTPException(404, f"Livrable inconnu: {fichier}")
        path = os.path.join(_DATA, "livrables", fichier)
        if not os.path.exists(path):
            raise HTTPException(404, ".docx non généré")
        return FileResponse(
            path, filename=fichier,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    return router
