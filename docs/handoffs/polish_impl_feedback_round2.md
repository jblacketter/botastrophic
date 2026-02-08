# Implementation Review: Polish

**Reviewer:** Codex
**Date:** 2026-02-06

## Files Reviewed
- dashboard/src/hooks/useActivityStream.ts
- dashboard/vite.config.ts
- dashboard/src/api/client.ts
- api/app/routes/stats.py
- docs/handoffs/polish_impl_handoff.md

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
- WebSocket URL now uses same-origin host, which is correct for nginx production.
- Memory endpoint paths now align between frontend and backend.
- Usage stats now reflect per-bot cap overrides.

### Issues Found
1. **HIGH** WebSocket fails in dev because Vite is not proxying `/ws`.
   - Location: `dashboard/src/hooks/useActivityStream.ts`, `dashboard/vite.config.ts`
   - Why: The WS client connects to `${window.location.host}/ws/activity` (port 3000 in dev), but the Vite dev server only proxies `/api`, not `/ws`. Result: no real-time updates in dev, violating the WebSocket success criterion.
   - Suggested fix: Add a Vite proxy entry for `/ws` with `ws: true`, or make the WS base URL configurable via env (e.g. `VITE_WS_URL`) and point to `ws://localhost:8000/ws/activity` in dev.

2. **HIGH** Reputation chart deliverable is still not implemented.
   - Location: `dashboard/src/components/StatsPanel.tsx`, `docs/handoffs/polish_impl_handoff.md`
   - Why: The plan and success criteria require a reputation chart “over time,” but the dashboard only shows token usage. The endpoint `/api/stats/reputation` returns current scores only, and no chart consumes it.
   - Suggested fix: Either implement a simple reputation chart (even current snapshot) and add time-series support (snapshot table or activity-log derived series), or explicitly defer and update scope/success criteria to match reality.

### Suggestions (non-blocking)
- Consider handling component unmount in `useActivityStream` to avoid reconnecting after cleanup (guard with a `isUnmounted` ref).
