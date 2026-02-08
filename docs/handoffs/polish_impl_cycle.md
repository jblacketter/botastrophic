# Review Cycle: Polish (Implementation)

**Phase:** Polish (Phase 4)
**Type:** Implementation Review
**Lead:** Claude
**Reviewer:** Codex

## Round 1
- **Date:** 2026-02-06
- **Handoff:** `docs/handoffs/polish_impl_handoff.md`
- **Impl log:** `docs/phases/polish_impl.md`
- **Status:** REQUEST CHANGES
- **Feedback:** `docs/handoffs/polish_impl_feedback_round1.md`
- **Blocking issues:**
  1. WebSocket client hardcodes port 8000, breaking production behind nginx
  2. Memory Explorer frontend calls `/api/bots/{id}/memory/*` but backend serves `/api/stats/bots/{id}/memory/*`
- **Fixes applied:**
  - Changed WebSocket URL from `hostname:8000` to `window.location.host` (respects nginx proxy)
  - Fixed frontend memory API calls to use `/api/stats/bots/{id}/memory/*` path
  - Usage stats now return per-bot cap overrides instead of always global defaults
  - Fixed `update_cost_cap` docstring to reference DELETE for reset (not null)

## Round 2
- **Date:** 2026-02-06
- **Handoff:** `docs/handoffs/polish_impl_handoff.md`
- **Impl log:** `docs/phases/polish_impl.md`
- **Status:** REQUEST CHANGES
- **Feedback:** `docs/handoffs/polish_impl_feedback_round2.md`
- **Blocking issues:**
  1. WebSocket fails in dev — Vite not proxying `/ws`
  2. Reputation chart deliverable not implemented
- **Fixes applied:**
  - Added `/ws` proxy entry to `vite.config.ts` with `ws: true`
  - Added `unmountedRef` guard to prevent reconnect after component cleanup
  - Added reputation tab to StatsPanel with bar chart (fetches from `/api/stats/reputation`)
  - Added `BotReputation` type and `fetchReputation()` to client.ts

## Round 3
- **Date:** 2026-02-06
- **Handoff:** `docs/handoffs/polish_impl_handoff.md`
- **Impl log:** `docs/phases/polish_impl.md`
- **Status:** REQUEST CHANGES
- **Feedback:** `docs/handoffs/polish_impl_feedback_round3.md`
- **Blocking issues:**
  1. Reputation chart shows only current snapshot, not "over time" as plan requires
- **Fixes applied:**
  - Added `reputation_score` to activity log details in heartbeat.py (time-series data source)
  - Added `GET /api/stats/reputation-history` endpoint (aggregates daily scores from activity logs)
  - Added `fetchReputationHistory()` and types to client.ts
  - Updated StatsPanel reputation tab with inline sparkline SVGs showing score trend per bot
  - Current scores + diverging bars still shown alongside sparklines

## Round 4
- **Date:** 2026-02-06
- **Handoff:** `docs/handoffs/polish_impl_handoff.md`
- **Impl log:** `docs/phases/polish_impl.md`
- **Status:** APPROVED
- **Feedback:** `docs/handoffs/polish_impl_feedback_round4.md`
- **Non-blocking suggestions:** Snapshot reputation in capped do_nothing logs; add indexing if history grows large
- **Result:** Implementation approved, Phase 4 complete
