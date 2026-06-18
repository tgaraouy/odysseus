#!/usr/bin/env bash
# provision.sh — preflight the pre-install infrastructure and collect the foundation
# data for a new Odysseus + MyOwnHealth install. See docs/PROVISIONING.md.
# Read-only on the system; writes .env, <bridge>/mcp/.env, data/settings.json only.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
REPO="$(pwd)"
say()  { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
miss() { printf '  \033[31mMISSING\033[0m  %s\n          fix: %s\n' "$1" "$2"; PREFLIGHT_OK=0; }
warn() { printf '  \033[33mWARN\033[0m  %s\n' "$1"; }
ask()  { local p="$1" d="${2:-}" v; if [ -n "$d" ]; then read -r -p "  $p [$d]: " v; echo "${v:-$d}"; else read -r -p "  $p: " v; echo "$v"; fi; }
asks() { local p="$1" v; read -r -s -p "  $p: " v; echo >&2; echo "$v"; }   # secret (hidden)
yes()  { local p="$1" v; read -r -p "  $p (y/N): " v; [[ "$v" =~ ^[Yy] ]]; }

PREFLIGHT_OK=1

# ───────────────────────────── A. PREFLIGHT ─────────────────────────────
say "A. Pre-install infrastructure"
# Docker is the common layer on every target. Run this on macOS (Terminal) or
# Windows (Git Bash — ships with the `git` prereq, so no WSL/Ubuntu needed).
case "$(uname -s)" in
  Darwin)               HOST_OS=mac;     pass "macOS ($(sw_vers -productVersion 2>/dev/null))";;
  Linux)                HOST_OS=linux;   pass "Linux ($(uname -r))";;
  MINGW*|MSYS*|CYGWIN*) HOST_OS=windows; pass "Windows ($(uname -s) — Git Bash)";;
  *)                    HOST_OS=other;   warn "unrecognized OS $(uname -s) — proceeding (Docker is the common layer)";;
esac

if docker info >/dev/null 2>&1; then pass "Docker Desktop running"
  else miss "Docker not running" "install/start Docker Desktop (docker.com)"; fi

if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  pass "Ollama reachable (:11434)"
  have_models="$(curl -fsS http://localhost:11434/api/tags | tr ',' '\n' | grep -oE '"name":"[^"]+"' | cut -d'"' -f4)"
  for m in gemma4 llama3.2-vision nomic-embed-text; do
    echo "$have_models" | grep -qi "$m" && pass "model: $m" || warn "model '$m' not pulled — run: ollama pull $m"
  done
else miss "Ollama not running" "install + start Ollama (ollama.com), then pull models"; fi

command -v uv >/dev/null 2>&1 && HAVE_UV=1 || HAVE_UV=0
if python3.12 --version >/dev/null 2>&1 || { python3 --version 2>&1 | grep -q '3\.12'; }; then
  pass "Python 3.12"
elif [ "$HAVE_UV" = 1 ]; then
  pass "Python 3.12 (uv will fetch it for the bridge venv)"
else
  miss "Python 3.12 not found" "install Python 3.12 (python.org) or uv (astral.sh/uv)"
fi
[ "$HAVE_UV" = 1 ] && pass "uv" || miss "uv not found" "curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v git >/dev/null 2>&1 && pass "git" || miss "git not found" "install git"

# Disk + RAM are best-effort (the probes differ per OS; never block on them).
if [ "$HOST_OS" = mac ]; then
  free_gb="$(df -g "$REPO" 2>/dev/null | awk 'NR==2{print $4}')"
  ram_gb=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
else
  free_gb="$(df -BG "$REPO" 2>/dev/null | awk 'NR==2{gsub(/[A-Za-z]/,"",$4); print $4}')"
  ram_gb=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo 2>/dev/null || echo 0) / 1048576 ))
fi
[ "${free_gb:-0}" -ge 25 ] 2>/dev/null && pass "disk: ${free_gb}GB free" || warn "disk low/unknown (${free_gb:-?}GB) — need ~25GB"
[ "${ram_gb:-0}" -ge 16 ] 2>/dev/null && pass "RAM: ${ram_gb}GB" || warn "RAM ${ram_gb:-?}GB (16GB+ recommended)"

if [ "$PREFLIGHT_OK" -ne 1 ]; then
  printf '\n\033[31mPreflight has MISSING items.\033[0m Resolve them, then re-run.\n'
  yes "Continue to collect foundation data anyway?" || exit 1
fi

# ───────────────────────────── B. FOUNDATION DATA ─────────────────────────────
if [ -f .env ] && ! yes "B. .env already exists — overwrite?"; then echo "Keeping existing .env."; exit 0; fi
say "B1. Identity & auth"
ADMIN_USER=$(ask "Admin username" "${USER:-admin}")
ADMIN_PASS=$(asks "Admin password (blank = auto-generate)")
# Default PUID/PGID to 1000 — the stack is built around uid 1000: the sandbox
# (code-exec) image runs as USER 1000:1000, so the app must drop to the SAME uid
# or they can't share the /ipc socket volume (the runner crash-loops with
# "bind: Address already in use" after a reboot, because a stale socket owned by
# one uid can't be cleaned by the other). The old "$(id -u)" default broke this on
# Windows, where Git Bash reports a large synthetic uid (e.g. 197609). Bind mounts
# (./data) are uid-agnostic on Docker Desktop, so 1000 is safe there; override
# only on native Linux if you need ./data owned by a specific host user.
PUID=$(ask "Host PUID" "1000"); PGID=$(ask "Host PGID" "1000")

say "B2/B3. LLM endpoints + network (defaults are usually fine)"
OLLAMA=$(ask "OLLAMA_BASE_URL" "http://host.docker.internal:11434/v1")
EMBED=$(ask "EMBEDDING_URL" "http://host.docker.internal:11434/v1/embeddings")
CHAT_MODEL=$(ask "Default chat model" "gemma4:latest")
VISION_MODEL=$(ask "Vision model" "llama3.2-vision:11b")
APP_PORT=$(ask "App port" "7000"); APP_BIND=$(ask "Bind address" "127.0.0.1")

say "B4. WHOOP wearable (optional — Enter to skip)"
WHOOP_ID=""; WHOOP_SECRET=""; WHOOP_REDIR=""
if yes "Configure WHOOP now?"; then
  WHOOP_ID=$(ask "WHOOP_CLIENT_ID"); WHOOP_SECRET=$(asks "WHOOP_CLIENT_SECRET")
  WHOOP_REDIR=$(ask "WHOOP_REDIRECT_URI" "http://localhost:${APP_PORT}/whoop/callback")
fi

say "B5. Search providers (optional — Enter to skip each)"
BRAVE=$(ask "DATA_BRAVE_API_KEY" ""); TAVILY=$(ask "TAVILY_API_KEY" ""); SERPER=$(ask "SERPER_API_KEY" "")

say "B6. Health foundation"
USER_NAME=$(ask "Your name (for the record)" "$ADMIN_USER")
TZ_=$(ask "Timezone" "$(readlink /etc/localtime 2>/dev/null | sed 's#.*/zoneinfo/##' || echo America/New_York)")
# The MyOwnHealth bridge is a SEPARATE repo (cloned per the runbook). Its WHOOP
# secret + venv live there, not in this Odysseus repo.
BRIDGE=$(ask "MyOwnHealth bridge repo path" "$HOME/myownhealth")

# ───────────────────────────── WRITE ─────────────────────────────
say "Writing config"
SXNG_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))' 2>/dev/null || openssl rand -hex 32)"
umask 177
cat > .env <<EOF
# Generated by provision.sh — $(date). chmod 600.
APP_BIND=${APP_BIND}
APP_PORT=${APP_PORT}
AUTH_ENABLED=true
SECURE_COOKIES=true
ODYSSEUS_ADMIN_USER=${ADMIN_USER}
ODYSSEUS_ADMIN_PASSWORD=${ADMIN_PASS}
PUID=${PUID}
PGID=${PGID}
OLLAMA_BASE_URL=${OLLAMA}
EMBEDDING_URL=${EMBED}
SEARXNG_SECRET=${SXNG_SECRET}
DATA_BRAVE_API_KEY=${BRAVE}
TAVILY_API_KEY=${TAVILY}
SERPER_API_KEY=${SERPER}
SANDBOX_FALLBACK_LOCAL=false
# Containerized MyOwnHealth bridge — \`docker compose up -d\` runs it too, so
# there's no launchd/systemd/WSL. COMPOSE_PROFILES turns the service on; the
# build context is the cloned bridge repo. WHOOP keys live here (compose passes
# them to the bridge container) — no separate mcp/.env needed.
COMPOSE_PROFILES=bridge
BRIDGE_REPO=${BRIDGE}
BRIDGE_OLLAMA_URL=http://host.docker.internal:11434
HEALTH_MCP_URL=http://bridge:8770/mcp
NTFY_TOPIC=Reminders
WHOOP_CLIENT_ID=${WHOOP_ID}
WHOOP_CLIENT_SECRET=${WHOOP_SECRET}
WHOOP_REDIRECT_URI=${WHOOP_REDIR}
EOF
chmod 600 .env; pass ".env (chmod 600)"

# The bridge repo is the Docker BUILD CONTEXT for the bridge service, so it must
# exist before `docker compose up -d --build`.
if [ -d "$BRIDGE" ]; then
  pass "bridge repo present ($BRIDGE)"
else
  warn "bridge repo not found at $BRIDGE — clone it before bringing up the stack:
          git clone https://github.com/tgaraouy/MyOwnHealth.git \"$BRIDGE\"
        (the bridge service builds from there; see RUNBOOK §3)"
fi

mkdir -p data
python3 - "$CHAT_MODEL" "$VISION_MODEL" "$USER_NAME" "$TZ_" <<'PY'
import json, os, sys
chat, vision, name, tz = sys.argv[1:5]
p = "data/settings.json"
s = json.load(open(p)) if os.path.exists(p) else {}
s.update({"default_model": chat, "vision_model": vision, "user_name": name, "timezone": tz})
json.dump(s, open(p, "w"), indent=2)
print("  PASS  data/settings.json")
PY

# ───────────────────────────── NEXT STEPS ─────────────────────────────
say "Next steps"
cat <<EOF
  1. Bring up everything (app + bridge):  docker compose up -d --build
                                          (the bridge builds from ${BRIDGE}; genesis auto-seeds,
                                          and supercronic runs the projection/weekly/apollo timers
                                          inside the container — no launchd/systemd)
  2. Register the bridge tools (once):    docker compose exec odysseus \\
                                            python scripts/seed_bridge_mcp.py
  3. Open:                                http://localhost:${APP_PORT}  (log in as ${ADMIN_USER})
  4. /health and /ledger populate after the bridge's first projection (~1 min).
$([ -z "$ADMIN_PASS" ] && echo '  NOTE: admin password was blank — the app generates a random one on first run and logs it.')
EOF
