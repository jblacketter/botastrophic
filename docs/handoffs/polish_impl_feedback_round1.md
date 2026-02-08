# Implementation Review: Polish

**Reviewer:** Codex
**Date:** 2026-02-06

## Files Reviewed
- api/app/routes/ws.py
- api/app/routes/config.py
- api/app/models/bot.py
- api/app/usage.py
- api/app/routes/stats.py
- api/app/orchestrator/heartbeat.py
- api/app/main.py
- dashboard/src/hooks/useActivityStream.ts
- dashboard/src/components/ActivityFeed.tsx
- dashboard/src/components/ConfigPanel.tsx
- dashboard/src/components/MemoryExplorer.tsx
- dashboard/src/components/StatsPanel.tsx
- dashboard/src/api/client.ts

## Checklist

### Correctness
- [ ] Implementation matches the plan
- [ ] Success criteria are met
- [ ] No obvious bugs
- [ ] Edge cases handled

### Code Quality
- [x] Code is readable and clear
- [x] No unnecessary complexity
- [x] Error handling is appropriate
- [ ] No hardcoded values that should be config

### Security
- [x] No injection vulnerabilities
- [x] No XSS vulnerabilities
- [x] Input validation present
- [x] Secrets not hardcoded

### Testing
- [ ] Tests exist for key functionality
- [ ] Tests pass
- [ ] Test coverage is reasonable

## Verdict: REQUEST CHANGES

## Feedback

### Looks Good
- WebSocket manager is simple and correctly cleans up failed connections.
- Config panel flows are coherent and map cleanly to API endpoints.
- Usage stats endpoint and dashboard display are consistent for demo scale.

### Issues Found
1. **HIGH** WebSocket client hardcodes port 8000, breaking production behind nginx.
   - Location: `dashboard/src/hooks/useActivityStream.ts`
   - Why: In production the dashboard is served by nginx on port 80 and proxies `/ws/*` to the API. Connecting to `ws://<host>:8000/ws/activity` will fail because port 8000 is not exposed.
   - Suggested fix: Use same-origin host (e.g. `${protocol}//${window.location.host}/ws/activity`) or an env-configured base URL that matches nginx.

2. **HIGH** Memory Explorer endpoints are mismatched between frontend and backend.
   - Location: `dashboard/src/api/client.ts`, `api/app/routes/stats.py`
   - Why: Frontend calls `/api/bots/{id}/memory/*`, but backend exposes `/api/stats/bots/{id}/memory/*`. This will 404 and the memory explorer won’t function, violating success criteria.
   - Suggested fix: Update frontend to call `/api/stats/bots/...` or add alias routes under `/api/bots/...`.

### Suggestions (non-blocking)
- `api/app/routes/stats.py` still returns global caps in usage responses even when per-bot overrides exist. Consider populating `token_cap`/`cost_cap_usd` per bot to match UI labels.
- `update_cost_cap` docstring says “set to null to reset” but the handler ignores explicit nulls; either document the DELETE endpoint or support null resets.
