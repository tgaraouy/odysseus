# Install runbook — Odysseus + MyOwnHealth on a fresh machine

Every step, in order, to take a bare machine to a running shell ready for the discovery phase.
Copy-paste friendly. Pairs with `docs/PROVISIONING.md` (what/why) and `docs/user-spec.md` (the
discovery itself).

> **One path for macOS and Windows.** Docker is the common layer; the whole stack — including the
> **MyOwnHealth health bridge** — runs as containers, so the same `docker compose up -d` works on
> both. No launchd, no systemd, **no WSL/Ubuntu**. The only per-OS difference is which terminal you
> type into and that Ollama runs natively on the host.
>
> - **macOS:** use **Terminal**.
> - **Windows:** use **Git Bash** (it ships with Git, a prerequisite below) — *not* PowerShell, so
>   the bash commands below run verbatim. Docker Desktop's own WSL2 backend runs the Linux
>   containers invisibly; you never open Ubuntu.
>
> *(The live Mac that built this still runs the bridge under launchd — that's a legacy mode, not
> what new installs do. See "Legacy: host bridge" at the bottom.)*

---

## 0 · Have ready
- An **admin username + password** you'll choose.
- *(optional)* WHOOP `client_id` / `client_secret`, any **search API keys** (Brave/Tavily/Serper).

## 1 · Install prerequisites (on the host)
Install these on the host OS (Windows or macOS), then verify from your terminal:
- **Docker Desktop** — docker.com. On **Windows**, accept the WSL2 backend it sets up (that's just
  Docker's engine — you won't use Ubuntu directly).
- **Ollama** — ollama.com (runs natively on the host: Ollama for Windows or for macOS).
- **Git** — git-scm.com. On Windows this also gives you **Git Bash**, the terminal you'll use.
- **uv** is **not** needed for new installs — the bridge's Python lives in its container.
- *(optional)* **Tailscale** — tailscale.com, for remote access during discovery.

```bash
docker info >/dev/null && echo "docker OK"
curl -fsS http://localhost:11434/api/tags >/dev/null && echo "ollama OK"
git --version
```

## 2 · Pull the local models
```bash
ollama pull gemma4
ollama pull llama3.2-vision:11b
ollama pull nomic-embed-text
```

## 3 · Get the code
```bash
# Odysseus — from your fork, the working branch:
git clone -b setup/local-docker-browser-mcp \
  https://github.com/tgaraouy/odysseus.git ~/odysseus/odysseus
# MyOwnHealth bridge (the bridge service builds its image from this repo):
git clone https://github.com/tgaraouy/MyOwnHealth.git ~/myownhealth
```
*(On Windows/Git Bash, `~` is your user folder, e.g. `C:\Users\you`. Keep both clones under it.)*

## 4 · Provision (preflight + foundation data)
```bash
cd ~/odysseus/odysseus
bash scripts/provision.sh    # checks infra, asks admin/keys/models, asks the bridge repo path
                             # → writes .env (incl. COMPOSE_PROFILES=bridge + BRIDGE_REPO), settings.json
```

## 5 · Bring up the whole stack (app + bridge)
```bash
docker compose up -d --build
docker compose ps            # all Up; 'bridge' Up and 'sandbox' Up (not Restarting)
```
`COMPOSE_PROFILES=bridge` in `.env` (written by provision) is what includes the bridge service.
The bridge image builds from `BRIDGE_REPO`; its **genesis auto-seeds** from
`mcp/charters/health.charter.yaml`, and **supercronic** runs the projection (10 min), weekly-query
(daily), and apollo (monthly) timers inside the container — the launchd/systemd replacement.

## 6 · Register the bridge tools (once)
Point the agent at the bridge's MCP endpoint (`http://bridge:8770/mcp` on the compose network):
```bash
docker compose exec odysseus python scripts/seed_bridge_mcp.py
docker compose restart odysseus     # reconnect to pick up the bridge tools
```
*(Or add it in the UI: Settings → MCP → add an HTTP server `http://bridge:8770/mcp`.)*

## 7 · Tailscale (remote access for discovery) — optional
```bash
tailscale up                 # log in
tailscale serve --bg 7000    # serve the app over HTTPS on your tailnet
tailscale serve status       # shows your https://<machine>.<tailnet>.ts.net URL (tailnet-only)
```
*(On Windows, run Tailscale on the host; point `tailscale serve` at the app's `127.0.0.1:7000`.)*

## 8 · Verify
```bash
docker compose logs odysseus | grep -iE "MyOwnHealth|tools via http" | tail -1   # bridge tools connected
docker compose logs bridge   | tail -20                                          # daemon + projection ran
```
- Open `http://localhost:7000` (or the Tailscale URL) → log in as your admin user.
- `/health` and `/ledger` render (they populate after the first projection, ~1 min).
  *(With `SECURE_COOKIES=true`, use HTTPS/Tailscale or localhost.)*
- WHOOP (if configured): visit `/whoop/callback` to finish OAuth.

## 9 · Discovery phase (the actual point)
This shell is now the **holder**. Run the intake from `docs/user-spec.md`:
1. **§1 Intent + §2 Outcomes** first — they drive everything.
2. **§3 Data** — sequence by *easy × impact*; bring in the high-impact/low-friction sources first.
3. **§4 Context** clearly; **§5 Boundaries** per dimension (incl. an *action* boundary).
4. **§6 Mandate** synthesized → confirmed by you → configures the shell.
*(When you want it agent-run: I'll build the specialized Intake agent + seed the spec into the instance.)*

---

## How the bridge runs in a container (reference)
- **Image:** `MyOwnHealth/mcp/Dockerfile` (python:3.12-slim). Installs the pinned bridge deps plus
  `chromadb-client==1.5.9` + `fastembed==0.8.0` (matched to the ChromaDB server digest Odysseus
  pins), and **supercronic** for the timers.
- **Process model:** `mcp/docker-entrypoint.sh` runs one projection on startup (so `/health` exists
  promptly), starts supercronic for the 3 timers, and execs the FastMCP daemon as the main process.
- **Wiring (compose `bridge` service):** ledger + generated `/health`,`/ledger` HTML live in the
  app's `./data` volume (mounted at `/odyssey-data`); the user's record + WHOOP tokens persist on
  the `myownhealth-data` named volume; gold tier → the shared `chromadb` service; reminders → the
  `ntfy` service; on-demand LLM tools → host Ollama via `host.docker.internal`.
- **Port :8770 is not published** — the bridge is reachable only on the compose network, never the
  LAN (preserves the original host-bridge security posture).

## Legacy: host bridge (the original live Mac)
The first Mac runs the bridge as a **host** process under **launchd** (`com.myownhealth.*` plists),
reaching the app via `host.docker.internal:8770`. New installs do **not** do this — they use the
container above. To keep a host bridge, leave `COMPOSE_PROFILES` unset, set up the venv
(`uv venv --python 3.12 mcp/.venv && uv pip install -r mcp/requirements.txt`), install the plists,
and register the MCP server at `http://host.docker.internal:8770/mcp`.

## Honest gaps to close
1. **provision.sh** doesn't auto-template/install the launchd plists for the legacy host-bridge mode
   (that mode is manual). The containerized path needs none of that.
2. **The bridge container runs as root** (first-party trusted backend that must write the shared
   data volume). A future pass can drop it to PUID/PGID with an entrypoint chown of the named volume.
3. **Charter/protocol are shared defaults** — per-user protocol still starts empty (by design).
