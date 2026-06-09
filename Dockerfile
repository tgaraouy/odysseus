FROM python:3.12-slim

# System deps. tmux is required by Cookbook for background downloads/serves.
# openssh-client is required for Cookbook remote server tests, setup, probes,
# downloads, and serves from Docker installs.
# git/cmake are required when Cookbook builds llama.cpp on first llama.cpp
# launch inside Docker.
# nodejs/npm provide npx for the optional built-in Browser MCP server.
# gosu lets the entrypoint drop privileges cleanly so signals still reach
# uvicorn directly (no extra shell layer like `su`/`sudo` would add).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    nodejs \
    npm \
    tmux \
    openssh-client \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Built-in Browser MCP (Playwright) -------------------------------------
# Bake @playwright/mcp + Chromium into the image so the optional Browser MCP
# server (src/builtin_mcp.py) registers at startup instead of being skipped.
# Without this the slim base lacks both the npx-cached package AND Chromium's
# shared libs, so the server self-disables with a "not installed" warning.
#
# Placement matters for two reasons:
#   * Runtime runs as PUID:PGID with HOME=/app (see docker/entrypoint.sh), so
#     the npx cache must sit at /app/.npm and browsers at /app/.cache/ms-
#     playwright (HOME's default) for `npx --no-install @playwright/mcp@latest`
#     to find them. Both are inside /app, which the entrypoint chowns to the
#     run user on boot; neither path is a bind-mount, so they stay in the image.
#   * The startup cache probe keys the npx cache on the literal spec string, so
#     pre-populating "@playwright/mcp@latest" here is exactly what the gate in
#     builtin_mcp.py:_is_npx_package_cached looks for.
#
# `--with-deps` re-runs apt (needs the package lists this layer restores) to
# pull Chromium's system libraries (libnss3, libgbm, libxkbcommon, …).
RUN apt-get update \
    && HOME=/app npm_config_cache=/app/.npm \
       npx -y @playwright/mcp@latest --version \
    && HOME=/app npm_config_cache=/app/.npm \
       npx -y playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache). Optional extras (PyMuPDF AGPL, etc.)
# are opt-in so the default image stays MIT-core; see requirements-optional.txt.
ARG INSTALL_OPTIONAL=false
COPY requirements.txt requirements-optional.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_OPTIONAL" = "true" ]; then pip install --no-cache-dir -r requirements-optional.txt; fi

# Local speech-to-text (STT) via faster-whisper (CTranslate2 + PyAV, CPU/int8).
# Enables Settings stt_provider=local for higher-accuracy offline dictation than
# the browser Web Speech API (better for medical terms — drug names, dosages).
# torch is intentionally omitted: services/stt/stt_service.py treats it as an
# optional CUDA probe and falls back to CPU when absent. Model weights download
# on first use into the mounted HF cache (./data/huggingface), so they persist.
RUN pip install --no-cache-dir faster-whisper

# Copy app code
COPY . .

# Create data directory (mount a volume here for persistence)
RUN mkdir -p data logs services/cache/search

# Entrypoint that drops to PUID/PGID (default 1000:1000) and repairs
# ownership on the bind-mounted /app/data and /app/logs. Without this,
# the container runs as root and writes root-owned files into host
# bind mounts — any later non-root run (or a host user trying to
# update them) silently fails on EPERM, breaking skill extraction,
# prefs persistence, mail attachments, etc.
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 7000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7000"]
