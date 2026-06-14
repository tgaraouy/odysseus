# Tier-B sandbox runner: a minimal, locked-down container that executes the
# agent's bash/python tool calls in isolation. See
# docs/security/bash-python-sandbox-scoping.md.
#
# Isolation is declared in docker-compose.yml (network_mode:none, read_only,
# tmpfs /work, cap_drop ALL, no-new-privileges, no secret/data/.ssh mounts,
# pids/mem/cpu limits). This image stays tiny: an interpreter, a shell, coreutils.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash coreutils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY runner.py /runner.py

# Non-root runner, uid 1000 to MATCH the app container's PUID. The shared
# `sandbox-ipc` volume is owned by the app's uid (1000) — its entrypoint chowns
# mounted volumes — so the runner must be 1000 to create/replace its socket there
# (cap_drop:ALL forbids a runtime chown). 65532 could not write the 1000-owned
# volume, so it crash-looped on bind with a stale socket present. 1000 is still
# non-root; isolation (no network, read-only rootfs, no mounts, dropped caps)
# is unchanged. /ipc 0775 + the runner's 0666 socket let both containers connect.
RUN mkdir -p /ipc /work \
    && chown 1000:1000 /ipc /work \
    && chmod 0775 /ipc /work

ENV RUNNER_SOCK=/ipc/runner.sock \
    RUNNER_WORKDIR=/work \
    PYTHONUNBUFFERED=1

USER 1000:1000

ENTRYPOINT ["python", "/runner.py"]
