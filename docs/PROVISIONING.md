# Provisioning a new laptop — Odysseus + MyOwnHealth

Everything a fresh machine needs to run a per-user, data-owned health agent. Two parts:
**(A) pre-install infrastructure** that must already exist, and **(B) foundation data** the
installer asks each user for. `scripts/provision.sh` checks A and collects B.

> Target: **macOS or Windows**. Docker is the common layer and the **MyOwnHealth bridge runs as a
> container** (its timers via supercronic), so there's no `launchd`/`systemd`/WSL dependency — the
> same `docker compose up -d` brings up everything on both. On Windows, run the steps from **Git
> Bash** (ships with Git); Docker Desktop's WSL2 backend runs the Linux containers invisibly.
> *(The original Mac still runs a legacy host bridge under launchd; see `docs/RUNBOOK.md`.)*

---

## A. Pre-install infrastructure (must exist before install)

| Component | Why it's needed | Required? | Get it |
|---|---|---|---|
| **macOS or Windows** | host OS; Docker Desktop runs the whole stack (incl. the bridge) | required | — |
| **Docker Desktop** (running) | runs the stack: `odysseus`, `chromadb`, `searxng`, `ntfy`, `sandbox`, `bridge` | **required** | docker.com |
| **Ollama** (native on host, running) | local LLMs — chat, vision, embeddings | **required** | ollama.com |
| └ **Ollama models pulled** | `gemma4` (chat), `llama3.2-vision:11b` (vision), an embedding model (`nomic-embed-text`) | **required** | `ollama pull <model>` |
| **Git** | clone the repos; on Windows also provides **Git Bash** (the terminal to use) | **required** | git-scm.com |
| **Python 3.12 + uv** | only for the **legacy host bridge** — the containerized bridge has its own Python | legacy only | astral.sh/uv |
| **Disk ≥ ~25 GB free** | Docker images + Ollama models + fastembed cache | required | — |
| **RAM ≥ 16 GB** | Docker + local LLM inference | recommended | — |
| **Tailscale** | secure remote access (tailnet, not public) | optional | tailscale.com |

`provision.sh` verifies each and reports `PASS` / `MISSING` with the fix command — it does not
install these for you (they need your admin consent / accounts).

---

## B. Foundation data (the installer ASKS the user for these)

### B1 — Identity & auth *(required)*
- **Admin username** (`ODYSSEUS_ADMIN_USER`)
- **Admin password** (`ODYSSEUS_ADMIN_PASSWORD`) — if blank, setup generates a random one and
  prints it once. Set a strong one.
- **Host PUID / PGID** — auto-detected (`id -u` / `id -g`); the container drops to this so
  bind-mounted files stay editable. (Also fixes the sandbox volume ownership.)

### B2 — LLM endpoints *(required; sensible defaults)*
- `OLLAMA_BASE_URL` = `http://host.docker.internal:11434/v1`
- `EMBEDDING_URL` = `http://host.docker.internal:11434/v1/embeddings`
- **Default chat model** (`gemma4:latest`), **vision model** (`llama3.2-vision:11b`) → written to
  `data/settings.json`.

### B3 — Network *(defaults, confirm)*
- `APP_BIND` (`127.0.0.1`), `APP_PORT` (`7000`), `SECURE_COOKIES` (`true`),
  `ALLOWED_ORIGINS`. `SEARXNG_SECRET` is auto-generated.

### B4 — Health wearable: WHOOP *(optional)*
- `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET`, `WHOOP_REDIRECT_URI` → written to the Odysseus
  **`.env`** (chmod 600); compose passes them into the bridge container. Skip to run without
  wearable sync. *(Legacy host bridge reads them from `<bridge>/mcp/.env` instead.)*

### B5 — Search & other providers *(optional)*
- Web search: `DATA_BRAVE_API_KEY`, `GOOGLE_API_KEY` + `GOOGLE_PSE_CX`, `TAVILY_API_KEY`,
  `SERPER_API_KEY` (SearXNG works without any of these).
- LLM: `OPENAI_API_KEY`, `HF_TOKEN` (optional — Ollama covers local).

### B6 — Health foundation seed
- **`charters/health.charter.yaml`** — ships with the repo; seeds the ledger **genesis** + the
  confidence taxonomy. (Not asked; shipped.)
- **`protocol.yaml`** — the user's medications/supplements protocol. Per-user: start empty, or
  import an existing one. Asked: *"import an existing protocol.yaml, or start fresh?"*
- **User's name** and **timezone** — for the record + scheduling.

### B7 — Paths *(auto-derived)*
- `BRIDGE_REPO` (the cloned MyOwnHealth path) is recorded in `.env` as the bridge's Docker build
  context. Inside the container the ledger, generated HTML, and user DB use fixed container paths
  (`/odyssey-data/...`, `/app/data/user/...`) mapped to volumes — no hardcoded host paths, no
  per-machine plist templating.

### B8 — Email *(optional)*
IMAP/SMTP host, port, username, app-password. Stored encrypted in-app (`src/secret_storage.py`),
configured in Settings after first login — `provision.sh` records intent; the user pastes the
app-password in the UI (never in `.env`).

### B9 — Calendar *(optional)*
CalDAV URL + credentials (or Google Calendar OAuth). Same handling as email — in-app, encrypted.

### B10 — Existing-user import *(optional)*
If migrating from an existing instance, point provisioning at an export to seed the new machine:
the **ledger** (`*.ledger.db` — hash-chained, verifiable on import), `protocol.yaml`, prior
`data/` (settings, memories, documents). Default = **fresh start** (empty template). *This is the
big fork — see §E and `docs/user-spec.md`.*

---

## C. Created on first run (generated, not asked)
`.env` (chmod 600, incl. `COMPOSE_PROFILES=bridge` + `BRIDGE_REPO` + WHOOP keys) · `data/auth.json`
(admin) · `data/settings.json` (models) · `data/.app_key` (secret storage) · the **ledger genesis**
from the charter (auto-seeded on the bridge's first run) · `SEARXNG_SECRET` · the `myownhealth-data`
volume (the user's record + WHOOP tokens + fastembed cache). No venv, no launchd plists — the
bridge's Python and timers (supercronic) live inside its container.

## D. Install order (what provision.sh / the operator runs)
1. **Preflight** — `scripts/provision.sh` checks section A, collects section B → writes `.env`
   (with `COMPOSE_PROFILES=bridge`, `BRIDGE_REPO`, WHOOP) + `data/settings.json`.
2. **Bring up everything** — `docker compose up -d --build` (app **and** bridge; genesis auto-seeds;
   supercronic runs the timers in-container).
3. **Register bridge tools** — `docker compose exec odysseus python scripts/seed_bridge_mcp.py`,
   then `docker compose restart odysseus`.
4. **Verify** — app reachable on `APP_PORT`; `/health` and `/ledger` render; bridge MCP connects
   (`tools via http`); WHOOP OAuth (if configured).

## E. Open questions for the product (not blocking v1)
- One-command bundle (a `.pkg` / signed installer) vs the script flow.
- Per-user data migration: does a new laptop start fresh, or import an existing user's ledger?
- Secrets handling at scale (today: `.env` files chmod 600; later: a vault / keychain).
