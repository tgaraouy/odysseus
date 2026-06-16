# Install runbook — Odysseus + ToufHealth on a fresh machine

Every step, in order, to take a bare machine to a running shell ready for the discovery phase.
Copy-paste friendly. Pairs with `docs/PROVISIONING.md` (what/why) and `docs/user-spec.md` (the
discovery itself).

> **Assumes macOS** (Mac mini or similar), admin access, ~25 GB free, internet.
> **Windows mini PC?** See the Windows section at the bottom — run it under **WSL2**, then this
> runbook applies almost verbatim. **Linux?** Same, with `systemd` instead of step 7's launchd.

---

## 0 · Have ready
- An **admin username + password** you'll choose.
- *(optional)* WHOOP `client_id` / `client_secret`, any **search API keys** (Brave/Tavily/Serper).

## 1 · Install prerequisites
```bash
# Docker Desktop — download from docker.com, launch it, then verify:
docker info >/dev/null && echo "docker OK"
# Ollama — download from ollama.com, launch it, then verify:
curl -fsS http://localhost:11434/api/tags >/dev/null && echo "ollama OK"
# uv (Python 3.12 manager):
curl -LsSf https://astral.sh/uv/install.sh | sh
# git + Tailscale: install Tailscale from tailscale.com; git via:
xcode-select --install 2>/dev/null || true
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
mkdir -p ~/odysseus && git clone -b setup/local-docker-browser-mcp \
  https://github.com/tgaraouy/odysseus.git ~/odysseus/odysseus
```
**ToufHealth bridge — has no git remote yet.** Copy `mcp/` + `charters/` from your main laptop to
`~/projects/health-experiment-studio/` (rsync/USB), **or** push it to a repo first and clone it.
*(Flag: this is a gap to close — see bottom.)*

## 4 · Provision (preflight + foundation data)
```bash
cd ~/odysseus/odysseus
bash scripts/provision.sh     # checks infra, asks for admin/keys/models → writes .env, mcp/.env, settings.json
```

## 5 · Bring up the stack
```bash
docker compose up -d --build
docker compose ps            # all Up; 'sandbox' Up (not Restarting)
```

## 6 · Set up the ToufHealth bridge
```bash
cd ~/projects/health-experiment-studio
uv venv --python 3.12 mcp/.venv
uv pip install --python mcp/.venv -r mcp/requirements.txt
# The ledger GENESIS auto-seeds from charters/health.charter.yaml on the bridge's first run — no manual seed.
```

## 7 · Install the bridge services (launchd timers — macOS)
The 4 plists carry absolute paths; template them to THIS machine, then load:
```bash
cd ~/projects/health-experiment-studio
for p in com.toufhealth.mcp com.toufhealth.projection com.toufhealth.weeklyquery com.toufhealth.apollo; do
  sed "s#/Users/tgaraouy/projects/health-experiment-studio#$HOME/projects/health-experiment-studio#g; \
       s#/Users/tgaraouy/odysseus/odysseus#$HOME/odysseus/odysseus#g" \
       "mcp/$p.plist" > "$HOME/Library/LaunchAgents/$p.plist"
  launchctl load -w "$HOME/Library/LaunchAgents/$p.plist"
done
launchctl list | grep toufhealth      # all four listed
```
*(If you put the repos elsewhere, adjust the two source paths in the `sed`.)*

## 8 · Tailscale (remote access for discovery)
```bash
tailscale up                 # log in
tailscale serve --bg 7000    # serve the app over HTTPS on your tailnet
tailscale serve status       # shows your https://<machine>.<tailnet>.ts.net URL (tailnet-only)
```

## 9 · Verify
```bash
docker compose logs odysseus | grep -i ToufHealth | tail -1   # expect: "... 24 tools via http"
```
- Open `http://localhost:7000` (or the Tailscale URL) → log in as your admin user.
- `/health` and `/ledger` render. *(With `SECURE_COOKIES=true`, use HTTPS/Tailscale or localhost.)*
- WHOOP (if configured): visit `/whoop/callback` to finish OAuth.

## 10 · Discovery phase (the actual point)
This shell is now the **holder**. Run the intake from `docs/user-spec.md`:
1. **§1 Intent + §2 Outcomes** first — they drive everything.
2. **§3 Data** — sequence by *easy × impact*; bring in the high-impact/low-friction sources first.
3. **§4 Context** clearly; **§5 Boundaries** per dimension (incl. an *action* boundary).
4. **§6 Mandate** synthesized → confirmed by you → configures the shell.
*(When you want it agent-run: I'll build the specialized Intake agent + seed the spec into the instance.)*

---

---

## Windows mini PC — run it under WSL2 (recommended)
Native Windows has a no-Docker launcher (`launch-windows.ps1`) but it **skips the sandbox /
chromadb / searxng services** — degraded and unhardened. For a faithful install, use **WSL2**
(a real Linux env), then steps 1–10 above apply almost verbatim from inside Ubuntu.

```powershell
# In Windows PowerShell (admin), once:
wsl --install -d Ubuntu       # installs WSL2 + Ubuntu; reboot if prompted
```
Then **install on the Windows host (not inside WSL):**
- **Docker Desktop for Windows** → Settings → Resources → WSL integration → enable for Ubuntu.
- **Ollama for Windows** (runs on the Windows host; `ollama pull` the 3 models from step 2).
- **Tailscale for Windows.**

Now open **Ubuntu (WSL2)** and run the runbook there:
- Steps 1 (uv, git only — Docker/Ollama already on the host), 2 (models already pulled), 3–6
  work as written. Ollama is reachable from containers via `host.docker.internal:11434` (same as
  Mac) and from WSL shell via `localhost:11434` (WSL2 forwards localhost to Windows).
- **Step 7 (services):** no launchd. Enable systemd in WSL2 (`/etc/wsl.conf` → `[boot]
  systemd=true`, then `wsl --shutdown` and reopen), and run the bridge + timers as **systemd
  user services / timers** (translate the 4 launchd plists). *Untested by us — flag if it fights.*
- **Step 8 (Tailscale):** `tailscale serve` from the Windows host pointing at the WSL2 app port.

> **Honest:** the Docker stack on WSL2 is well-trodden; the **bridge-as-a-systemd-service inside
> WSL2** is the one piece we haven't run. Expect to iterate there. Paths become
> `/home/<you>/...` (Linux), not `/Users/...`.

## Honest gaps to close (so this is a clean kit)
1. **ToufHealth has no git remote** — step 3 needs a manual copy. Fix: push `mcp/` to a repo.
2. **provision.sh doesn't auto-template/install the plists** (step 7 is manual) — fold it in.
3. **macOS only** for step 7 — add the Linux/systemd path if the mini PC isn't a Mac.
4. **Charter/protocol are shared defaults** — per-user protocol still starts empty (by design).
