# Provisioning a new laptop — Odysseus + MyOwnHealth

Everything a fresh machine needs to run a per-user, data-owned health agent. Two parts:
**(A) pre-install infrastructure** that must already exist, and **(B) foundation data** the
installer asks each user for. `scripts/provision.sh` checks A and collects B.

> Target: **macOS** (Apple Silicon or Intel). The bridge runtime uses macOS `launchd` timers.
> Linux is possible but the timer/service layer differs — out of scope for v1.

---

## A. Pre-install infrastructure (must exist before install)

| Component | Why it's needed | Required? | Get it |
|---|---|---|---|
| **macOS** | host OS; `launchd` timers run the bridge/projection | required | — |
| **Docker Desktop** (running) | runs the stack: `odysseus`, `chromadb`, `searxng`, `ntfy`, `sandbox` | **required** | docker.com |
| **Ollama** (native on host, running) | local LLMs — chat, vision, embeddings | **required** | ollama.com |
| └ **Ollama models pulled** | `gemma4` (chat), `llama3.2-vision:11b` (vision), an embedding model (`nomic-embed-text`) | **required** | `ollama pull <model>` |
| **Python 3.12** | MyOwnHealth bridge runtime | required *(health features)* | python.org |
| **uv** | builds the bridge venv (`mcp/.venv`) | required *(health features)* | astral.sh/uv |
| **Git** | clone the repos | required | — |
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
- `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET`, `WHOOP_REDIRECT_URI` → written to **`mcp/.env`**
  (chmod 600). Skip to run without wearable sync.

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
- The new machine's home path is substituted into the `launchd` plists and `LEDGER_DB`
  (`<repo>/data/ledger/health.ledger.db`). No hardcoded `/Users/tgaraouy/...`.

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
`.env` (chmod 600) · `mcp/.env` (chmod 600) · `data/auth.json` (admin) · `data/settings.json`
(models) · `data/.app_key` (secret storage) · the **ledger genesis** from the charter · the
bridge venv (`mcp/.venv`) · the four `launchd` timers (path-substituted) · `SEARXNG_SECRET`.

## D. Install order (what provision.sh / the operator runs)
1. **Preflight** — `scripts/provision.sh` checks section A, collects section B → writes `.env`,
   `mcp/.env`, `data/settings.json`.
2. **Bring up the stack** — `docker compose up -d --build`.
3. **Bridge** — `uv venv --python 3.12 mcp/.venv && uv pip install -r mcp/requirements.txt`,
   seed the ledger genesis, install the `launchd` timers.
4. **Verify** — app reachable on `APP_PORT`; `/health` and `/ledger` render; bridge MCP connects
   (24 tools); WHOOP OAuth (if configured).

## E. Open questions for the product (not blocking v1)
- One-command bundle (a `.pkg` / signed installer) vs the script flow.
- Per-user data migration: does a new laptop start fresh, or import an existing user's ledger?
- Secrets handling at scale (today: `.env` files chmod 600; later: a vault / keychain).
