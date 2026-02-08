# Review Cycle: Polish (Plan)

**Phase:** Polish (Phase 4)
**Type:** Plan Review
**Lead:** Claude
**Reviewer:** Codex

## Round 1
- **Date:** 2026-02-06
- **Plan:** `docs/phases/polish.md`
- **Status:** REQUEST CHANGES
- **Feedback:** `docs/handoffs/polish_plan_feedback.md`
- **Blocking issues:**
  1. Per-bot cost cap storage undefined
  2. WebSocket broadcast ambiguous with multiple workers
- **Fixes applied:**
  - Added nullable `daily_token_cap`/`daily_cost_cap_usd` columns to Bot model with NULL-means-global-default resolution
  - Committed to single uvicorn worker (in-memory ConnectionManager + APScheduler + SQLite)
  - Added memory endpoint pagination (limit/offset)
  - Added WebSocket fallback UX (badge, exponential backoff, 10s polling fallback)

## Round 2
- **Date:** 2026-02-06
- **Plan:** `docs/phases/polish.md` (revised)
- **Status:** APPROVED
- **Non-blocking suggestions:** Warm pagination per category, cost cap "Default vs Custom" label
- **Result:** Plan approved, ready for implementation
