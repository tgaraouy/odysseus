# Residual: API-token scope does not constrain the agent's tools

**Status:** Accepted / deferred. Documented as a known residual; implement if/when
limited-scope companion tokens are actually issued (see Trigger).
**Date:** 2026-06-14. Outcome of the #6 hardening review.

## What IS enforced today (verified in code)
- **SSRF (R-2): closed.** `/api/v1/chat` validates token-supplied `base_url` via
  `src/url_security.py:validate_public_http_url` — blocks non-http(s) schemes, `localhost`/
  `metadata`/`.internal`/`.lan`/etc., all private/loopback/link-local/CGNAT/reserved IPs
  (incl. `169.254.169.254` and `host.docker.internal`), DNS-resolves with all-IPs-must-be-public,
  fail-closed; httpx does not follow redirects. Tests: `tests/test_url_safety.py`,
  `tests/test_webhook_ssrf_resilience.py`. Residual: DNS-rebinding TOCTOU only.
- **Per-capability token scopes exist and are enforced on the API surface.**
  `routes/api_token_routes.py:ALLOWED_SCOPES` = `chat`, `todos:read|write`,
  `documents:read|write`, `email:read|draft|send`, `calendar:read|write`, `memory:read|write`.
  Enforced on `routes/codex_routes.py` (each route checks `request.state.api_token_scopes`
  against a required scope set) and `/v1/chat` (requires `chat`).

## The residual gap
**Rule that is *not* enforced:** "an API token may only exercise capabilities within its
scopes." It holds for *direct API endpoints*, but **not** for *agent-mediated* actions.

Once a `chat`-scoped token drives the agent (`POST /api/v1/chat`), the agent executes tool
calls with the **token owner's full privileges** via the internal-tool loopback
(`core/middleware.py`). The token's scope list is never intersected with the agent's available
tools. So a `chat`-only token, if the owner is admin, can be conversationally steered into
`bash`, `send_email`, `write_file`, etc.

**Impact:** a leaked or compromised companion/mobile token is as powerful as the owner — the
scope is cosmetic for anything the agent can do.

## Trigger (when this matters)
Only when **limited-scope API tokens are issued** (companion/mobile/integration tokens). If the
system is used solely through the owner's own authenticated web session, there is no
lower-privilege token to contain, and this residual is inert.

## Recommended fix (implementation-ready)
Gate the agent's tools by the authenticating token's scopes — **API-token sessions only**, never
the owner's own session.

1. In the chat path (`routes/chat_routes.py`), read `request.state.api_token_scopes`.
2. If present (i.e. the request authenticated via an API token), compute a scope-allowed tool
   allowlist and add its complement to the agent loop's existing `disabled_tools`
   (`src/agent_loop.py` already enforces `disabled_tools`; this is an additive hook, like
   `blocked_tools_for_owner`).
3. **Fail-closed:** a token with no matching scope for a tool → that tool is disabled.

Starter scope → tool map (tune as policy):

| scope | unlocks (agent tools) |
|---|---|
| `chat` (only) | conversational + read-only: `web_search`, `web_fetch`, `read_file`, `grep`, `glob`, `ls` — **no** shell, write, send, or `manage_*` |
| `documents:read` / `:write` | `read`/`create`/`edit_document` |
| `email:read` / `:draft` / `:send` | `list_emails`/`read_email` · `reply`/draft · `send_email` |
| `calendar:read` / `:write` | `manage_calendar` (read vs mutate) |
| `memory:read` / `:write` | `manage_memory` (read vs mutate) |
| `todos:read` / `:write` | `manage_tasks` |
| (never via token) | `bash`, `python`, `manage_settings/endpoints/mcp/tokens/webhooks`, model serving |

The owner's own web session carries no `api_token_scopes`, so it is unaffected and keeps full
access. Pure-`chat` tokens become genuinely safe: even a fully-obeyed injection can't reach a
privileged sink because the tool isn't in the agent's set for that session.

## Decision
Deferred. The owner uses their own admin session; no limited-scope companion tokens are in use
today. Revisit before issuing any. Cross-ref: `THREAT_MODEL.md` Known Gaps #4.
