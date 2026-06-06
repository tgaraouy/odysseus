# Local Docker Deployment — Setup Reference

Configuration performed on **2026-06-05** for the local Docker Compose deployment
(`http://127.0.0.1:7000`). This documents every change made, why, and how to verify
or redo it. Host: macOS. LLM: Ollama running natively on the host.

> **Files touched:** `Dockerfile` (committed), `.env` (gitignored), `data/auth.json`
> and `data/settings.json` (gitignored runtime state). Only the `Dockerfile` change
> is in version control; the rest live in your local `data/` and `.env`.

---

## TL;DR — what got configured

| Area | Result | Where it lives |
|---|---|---|
| Login / admin auth | `admin` password reset; login works | `data/auth.json` |
| LLM (Ollama) | Reachable from container via `host.docker.internal` | `.env` → `OLLAMA_BASE_URL` |
| Embeddings | Same Ollama endpoint | `.env` → `EMBEDDING_URL` |
| Default chat model | `gemma4:latest` | `data/settings.json` |
| Vision model | `llama3.2-vision:11b` | `data/settings.json` |
| Web search | SearXNG (self-hosted, no key) | `data/settings.json` (default) |
| Voice TTS/STT | Browser provider (Web Speech API) | `data/settings.json` |
| Browser MCP | Baked into image; 29 tools at startup | `Dockerfile` |

---

## 1. Login / admin auth

**Symptom:** `POST /api/auth/login` returned `401`. Setup log showed
`[skip] auth.json already exists`.

**Cause:** On first boot `ODYSSEUS_ADMIN_PASSWORD` was unset, so the non-interactive
Docker setup (`setup.py:create_default_admin`) fell back to a **random** password
(`secrets.token_urlsafe(18)`) printed once to logs and otherwise unknown. Re-enabling
the env var afterward does nothing because `auth.json` already exists and setup skips it.

**Fix applied:** Reset the existing `admin` user's bcrypt hash in `data/auth.json`,
then restart so the app reloads it (credentials are cached in memory at startup).

To reset again in the future:

```bash
# Stop first so the app's shutdown flush doesn't clobber the edit (see Gotchas).
docker stop odysseus-odysseus-1
python3 - <<'PY'
import json, bcrypt
p = "data/auth.json"
d = json.load(open(p))
d["users"]["admin"]["password_hash"] = bcrypt.hashpw(b"YOUR_NEW_PASSWORD", bcrypt.gensalt()).decode()
json.dump(d, open(p, "w"), indent=2)
PY
docker start odysseus-odysseus-1
```

> Change the password in-app (Settings) after logging in so it isn't sitting in a file.

---

## 2. LLM (Ollama) + embeddings

**Symptom:** No models available in the app even though Ollama runs fine on the host.

**Cause:** `.env` had `LLM_HOST=localhost`. Inside Docker, `localhost` is the
**container itself**, not the Mac host. Verified: container → `localhost:11434`
unreachable; container → `host.docker.internal:11434` reachable.

**Fix applied** — uncommented/added in `.env`:

```ini
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
EMBEDDING_URL=http://host.docker.internal:11434/v1/embeddings
```

Requires recreating the container (env is injected at container **creation**, not restart):

```bash
docker compose up -d odysseus
```

Host Ollama models discovered: `gemma4:latest`, `llama3.2-vision:11b`, `minicpm-v:8b`.

---

## 3. Default models

After the Ollama fix, the app auto-discovered the endpoint
(`default_endpoint_id` derived from the URL) and auto-picked `minicpm-v:8b` — a
vision model being used as the general chat default.

**Fix applied** in `data/settings.json`:

```json
{
  "default_model": "gemma4:latest",
  "vision_model": "llama3.2-vision:11b",
  "vision_enabled": true
}
```

All three models share the same Ollama endpoint, so only the model **name** is needed —
vision resolution falls back to `default_endpoint_id` when `vision_endpoint_id` is unset
(`src/endpoint_resolver.py`).

---

## 4. Voice (TTS / STT)

**Decision:** Used the **`browser`** provider for both — it uses the browser's built-in
Web Speech API (client-side), needs **zero server dependencies**. The slim image does
not ship `kokoro` (local TTS) or `faster_whisper` (local STT), so the `local` provider
would not work without a Dockerfile change.

**Applied** in `data/settings.json`:

```json
{
  "tts_enabled": true,  "tts_provider": "browser",
  "stt_enabled": true,  "stt_provider": "browser"
}
```

> Browser voice works well in Chrome/Edge, is limited in Firefox/Safari. For
> higher-quality local voice, add `kokoro` + `faster-whisper` via a Dockerfile layer
> (not done), or plug an OpenAI-compatible voice API key into Settings.

---

## 5. Web search

No change needed — `search_provider` is already `searxng`, which is bundled in the
Compose stack and needs **no API key**. Premium providers (Brave / Tavily / Serper /
Google PSE) require your own key, added in Settings.

---

## 6. Browser MCP (Playwright) — Dockerfile change

**Goal:** Make the optional Built-in Browser MCP server register at startup instead of
self-disabling.

**Why it needed an image change (not a runtime install):**
- The slim base lacked **all** of Chromium's shared libs (`libnss3`, `libgbm`,
  `libxkbcommon`, …).
- The app gates the server on an npx cache probe
  (`src/builtin_mcp.py:_is_npx_package_cached` → `npx --no-install @playwright/mcp@latest --version`).
- The npx cache (`/app/.npm`) is **not** a mounted volume, so any ad-hoc `docker exec`
  install would vanish on the next recreate.

**Change made** — a cached layer after `WORKDIR /app` in `Dockerfile`:

```dockerfile
# (full comment block is in the Dockerfile)
RUN apt-get update \
    && HOME=/app npm_config_cache=/app/.npm \
       npx -y @playwright/mcp@latest --version \
    && HOME=/app npm_config_cache=/app/.npm \
       npx -y playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*
```

`HOME=/app` makes both the npx cache (`/app/.npm`) and the Chromium download
(`/app/.cache/ms-playwright`) land where the runtime user finds them by default — no
`PLAYWRIGHT_BROWSERS_PATH` override needed.

**Why these paths:** The app runs as a non-root user with `HOME=/app`
(`docker/entrypoint.sh`), and the entrypoint chowns the whole `/app` tree to that user
on boot. So:
- npx cache → `/app/.npm` (HOME default; matches the startup probe).
- Chromium → `/app/.cache/ms-playwright` (HOME default).
- Both are inside `/app`, are **not** bind-mounts → persist in the image and survive
  every `docker compose up` / recreate.
- `--with-deps` re-runs apt to pull Chromium's system libraries.

**Rebuild + verify:**

```bash
docker compose build odysseus
docker compose up -d odysseus
docker logs odysseus-odysseus-1 2>&1 | grep -i browser
# Expect: "Built-in NPX server registered: Built-in: Browser"  (29 tools)
```

> Cost: image grows ~400–500 MB. A normal rebuild reuses the cached layer; a
> `--no-cache` build re-downloads Chromium.

---

## Gotchas discovered (read before editing config)

1. **`settings.json` is flushed on shutdown.** The running app holds settings in memory
   and writes them back to disk on SIGTERM (`docker stop` / `docker restart`). Editing
   the file while the app is **running** then restarting gets your edit **clobbered**.
   → **Stop the container first**, edit `data/settings.json` on the host, then `start`.

2. **`auth.json` is cached at startup.** A password change on disk needs a restart to
   take effect (but see #1 — stop, edit, start).

3. **`localhost` ≠ host inside Docker.** Use `host.docker.internal` for host services
   (Ollama, LM Studio). The Compose network names (`searxng`, `chromadb`, `ntfy`) are
   used for in-stack services automatically.

4. **`.env` changes need recreate, not restart.** Env vars are injected at container
   creation: `docker compose up -d odysseus` (a bare `docker restart` keeps the old env).

5. **`ODYSSEUS_ADMIN_PASSWORD` only applies on first boot**, when no `auth.json` exists.

---

## Quick health check

```bash
# All backing services reachable from the app container:
docker exec odysseus-odysseus-1 sh -c '
for u in http://searxng:8080 http://chromadb:8000/api/v2/heartbeat \
         http://ntfy:80 http://host.docker.internal:11434/api/tags; do
  curl -s -o /dev/null -w "%{http_code} $u\n" --max-time 4 "$u"; done'

# Effective app settings:
docker exec odysseus-odysseus-1 python3 -c \
'import json;s=json.load(open("/app/data/settings.json"));
print({k:s.get(k) for k in ["default_model","vision_model","tts_provider","stt_provider","search_provider"]})'
```
