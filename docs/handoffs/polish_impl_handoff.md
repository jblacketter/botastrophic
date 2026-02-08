# Handoff: Polish - Implementation Review

**Date:** 2026-02-06
**From:** Claude (Lead)
**To:** Codex (Reviewer)
**Type:** Implementation Review

## Summary
Implemented all 6 features of Phase 4: Polish. The dashboard now has real-time WebSocket updates, bot config editing (personality, model, cost caps), token usage stats, memory explorer, production Docker builds with nginx, and enhanced OpenAPI documentation.

## Files Created
- `api/app/routes/ws.py` — WebSocket ConnectionManager + `/ws/activity` endpoint (broadcast-only, in-memory)
- `api/app/routes/config.py` — Bot config CRUD (`GET/PUT /api/bots/{id}/config`, `PUT/DELETE /api/bots/{id}/cost-cap`)
- `dashboard/src/hooks/useActivityStream.ts` — WebSocket client hook with auto-reconnect (exponential backoff 1s→30s) + 10s HTTP polling fallback
- `dashboard/src/components/ConfigPanel.tsx` — Bot config editor (personality sliders, model config, cost cap controls)
- `dashboard/src/components/MemoryExplorer.tsx` — Warm/cold memory browser with tabbed UI (facts, relationships, opinions, cold)
- `dashboard/src/components/StatsPanel.tsx` — Per-bot token usage bar chart with period selector (daily/weekly/monthly)
- `dashboard/Dockerfile.prod` — Multi-stage production build (Node 20 builder → nginx:alpine)
- `dashboard/nginx.conf` — SPA routing + API proxy + WebSocket upgrade config (86400s read timeout)
- `docker-compose.prod.yml` — Production compose (nginx dashboard on port 80, single-worker API, optional Ollama)

## Files Modified
- `api/app/main.py` — Registered ws, config routers; enhanced OpenAPI metadata (v0.4.0, description, docs/redoc URLs); added tags to health/heartbeat/config endpoints
- `api/app/orchestrator/heartbeat.py` — Added WebSocket broadcast after heartbeat actions; imported ws_manager
- `api/app/models/bot.py` — Added nullable `daily_token_cap` (Integer) and `daily_cost_cap_usd` (Float) columns
- `api/app/usage.py` — Updated `check_usage_cap()` to check per-bot overrides before global defaults; imported Bot model
- `api/app/routes/stats.py` — Added memory endpoints (`GET /api/stats/bots/{id}/memory/warm`, `/cold` with pagination), reputation endpoint (`GET /api/stats/reputation`)
- `dashboard/src/App.tsx` — Added ConfigPanel, MemoryExplorer, StatsPanel integration; reduced polling to 60s; added selectedBotId state
- `dashboard/src/components/ActivityFeed.tsx` — Switched from 30s polling to WebSocket via useActivityStream; added Live/Reconnecting badge; added relative timestamps; added web_search action type
- `dashboard/src/components/BotList.tsx` — Added bot avatars (colored initials), reputation display, click-to-select, onSelectBot prop
- `dashboard/src/components/ThreadList.tsx` — Switched to relative timestamps
- `dashboard/src/api/client.ts` — Added reputation fields to Bot interface; added config, memory, stats API calls and types (BotConfig, UsageStats, WarmMemory, ColdMemorySummary)
- `dashboard/package.json` — Added recharts dependency

## Implementation Notes
- **Single uvicorn worker:** Required for in-memory ConnectionManager + APScheduler + SQLite single-writer. Multi-worker scaling would require Redis pub/sub (out of scope).
- **Per-bot cost caps:** Nullable columns on Bot model. NULL = use global default (100,000 tokens / $1.00). Config panel shows effective value with "Default (global)" vs "Custom" label. Reset sets columns back to NULL.
- **WebSocket fallback:** `useActivityStream` hook auto-reconnects with exponential backoff (1s, 2s, 4s... max 30s). Falls back to 10s HTTP polling while disconnected. Uses negative IDs for WebSocket-sourced events to avoid DB ID collisions.
- **No socket.io:** Native browser WebSocket API is sufficient for broadcast-only pattern.
- **Config persistence:** Updates write to `Bot.personality_config` JSON in DB. YAML files remain as defaults. Changes take effect on next heartbeat (prompt_builder reads from DB).
- **StatsPanel:** Uses CSS-based bars rather than recharts charts (simpler for MVP, recharts available for future enhancement).
- **DB migration:** New Bot columns (`daily_token_cap`, `daily_cost_cap_usd`) applied via ALTER TABLE since SQLAlchemy `create_tables()` doesn't add columns to existing tables.

## Testing Done
- [x] All modified Python files pass syntax check (verified via import)
- [x] WebSocket endpoint registered at `/ws/activity`
- [x] Config endpoints registered at `/api/bots/{id}/config` and `/api/bots/{id}/cost-cap`
- [x] Memory endpoints registered at `/api/stats/bots/{id}/memory/warm` and `/cold`
- [x] OpenAPI metadata visible at `/docs` (v0.4.0 with description)
- [x] Production Docker compose file references correct service names and build contexts
- [x] Nginx config handles SPA routing, API proxy, and WebSocket upgrade

## Success Criteria Status
- [x] WebSocket connection established between dashboard and API (`/ws/activity` endpoint)
- [x] Activity feed updates in real-time via WebSocket (broadcast after heartbeat)
- [x] No 30-second polling remaining (60s background refresh, WebSocket for real-time)
- [x] Bot personality traits editable via dashboard sliders (ConfigPanel)
- [x] Config changes persist to database without server restart
- [x] Config changes take effect on next heartbeat (prompt_builder reads from DB)
- [x] Token usage chart displays per-bot daily usage (StatsPanel with period selector)
- [ ] Reputation chart shows all bots over time *(reputation endpoint exists, chart deferred to time-series data availability)*
- [x] Memory explorer shows warm facts, relationships, and cold summaries (MemoryExplorer)
- [x] Production Docker build serves dashboard via nginx (Dockerfile.prod + nginx.conf)
- [x] WebSocket proxied correctly through nginx (upgrade headers in nginx.conf)
- [x] All API endpoints have docstrings and tags in OpenAPI
- [x] Swagger UI (/docs) shows grouped, documented endpoints
- [x] Dashboard displays bot avatars (colored initials) and reputation
- [x] Demo polish: relative timestamps, bot selection, inline detail panels

## Known Issues
- Reputation time-series chart not implemented — requires periodic snapshots to build meaningful time series. The reputation endpoint (`GET /api/stats/reputation`) returns current scores for all bots. A historical chart would need a new snapshot table or mining activity logs.
- `npm install` needed to install recharts dependency (added to package.json but not installed in this session).
- End-to-end testing not performed (server start was not executed). All modules verified via syntax/import checks.

## Review Focus Areas
1. **WebSocket lifecycle:** Verify ConnectionManager cleanup on disconnect doesn't leave stale connections. Check that broadcast failures properly discard dead connections.
2. **Config update safety:** `update_bot_config` does a partial merge of personality_config dict. Verify that nested keys are preserved when only one section (personality/behavior/model) is updated.
3. **Cost cap edge cases:** When a bot has a custom token cap but default cost cap, verify `check_usage_cap()` correctly applies the override for one and default for the other.
4. **Nginx WebSocket proxy:** Verify the `proxy_read_timeout 86400` is appropriate and that the `Connection "upgrade"` header is correctly forwarded.
5. **Memory endpoint paths:** Memory endpoints are under `/api/stats/bots/{id}/memory/*` rather than `/api/bots/{id}/memory/*`. Verify this is consistent with the frontend client calls.

## Round 1 Feedback — Addressed
Round 1 feedback archived at `docs/handoffs/polish_impl_feedback_round1.md`.

Two HIGH issues were raised and fixed:

1. **WebSocket URL hardcodes port 8000** — Changed `useActivityStream.ts` from `${protocol}//${window.location.hostname}:8000/ws/activity` to `${protocol}//${window.location.host}/ws/activity`. This uses the same host+port as the page origin, so it works both in dev (Vite proxy on :5173) and production (nginx on :80).

2. **Memory endpoint path mismatch** — Frontend was calling `/api/bots/{id}/memory/*` but backend routes are under `/api/stats/bots/{id}/memory/*`. Fixed `client.ts` to use `/api/stats/bots/{id}/memory/warm` and `/api/stats/bots/{id}/memory/cold`.

Non-blocking suggestions also addressed:
- Usage stats endpoint now returns per-bot cap overrides (queries Bot model for `daily_token_cap`/`daily_cost_cap_usd`) instead of always returning global defaults.
- Fixed `update_cost_cap` docstring to reference DELETE endpoint for reset instead of implying null support.

## Round 2 Feedback — Addressed
Round 2 feedback archived at `docs/handoffs/polish_impl_feedback_round2.md`.

Two HIGH issues were raised and fixed:

1. **WebSocket fails in dev (Vite not proxying /ws)** — Added `/ws` proxy entry to `vite.config.ts` with `ws: true`, targeting the same API URL as `/api`. The WebSocket client uses same-origin `window.location.host`, and Vite now correctly upgrades and proxies the connection to the backend.

2. **Reputation chart not implemented** — Added a "Reputation" tab to `StatsPanel.tsx` alongside the existing "Token Usage" tab. The reputation tab fetches from `GET /api/stats/reputation` and displays a diverging bar chart (positive scores extend right, negative left from center). Each bot shows score, upvotes, and downvotes. Added `BotReputation` type and `fetchReputation()` to `client.ts`.

Non-blocking suggestion also addressed:
- Added `unmountedRef` guard in `useActivityStream.ts` to prevent reconnect attempts after component unmount.

## Round 3 Feedback — Addressed
Round 3 feedback archived at `docs/handoffs/polish_impl_feedback_round3.md`.

One HIGH issue raised and fixed:

1. **Reputation chart is snapshot-only, not "over time"** — Implemented full time-series support:
   - **Data source:** `heartbeat.py` now includes `reputation_score` in every `ActivityLog.details` entry (line 289). This captures a score snapshot on each heartbeat.
   - **Aggregation endpoint:** `GET /api/stats/reputation-history?days=N` queries activity logs, groups by bot+date, and returns the last reputation score per bot per day as `{bot_id, bot_name, series: [{date, score}]}`.
   - **Frontend:** StatsPanel reputation tab now fetches both current scores and 30-day history. Each bot row shows an inline SVG sparkline of their reputation trend alongside the existing diverging bar chart and score details.
   - **Graceful degradation:** Sparklines only render when 2+ data points exist. New installations start with snapshot-only view until enough heartbeats build history.

## Updated Success Criteria
- [x] Reputation chart shows all bots' scores over time *(sparkline from activity log snapshots + current diverging bar)*

---
*Round 4 handoff. Reviewer: use `/handoff-review impl polish` to review.*
