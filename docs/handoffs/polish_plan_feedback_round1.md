# Plan Review: Polish

**Reviewer:** Codex
**Date:** 2026-02-06

## Checklist

### Scope & Feasibility
- [x] Scope is clearly defined
- [x] Scope is appropriately sized for one phase
- [x] Technical approach is feasible
- [x] Dependencies are correctly identified

### Technical Design
- [x] Architecture decisions are sound
- [x] File structure is logical
- [x] Follows project conventions
- [ ] No over-engineering

### Success Criteria
- [x] Criteria are specific and testable
- [x] Criteria match the stated scope
- [x] All major deliverables have criteria

### Risks & Questions
- [x] Major risks are identified
- [x] Mitigations are reasonable
- [x] Open questions are appropriate

## Verdict: REQUEST CHANGES

## Feedback

### Agreements
- Clear, complete scope with a good implementation order.
- WebSocket + config + stats + production build is the right Phase 4 focus.
- Success criteria are measurable and tied to deliverables.

### Suggested Changes
- Consider adding pagination/filtering to the memory endpoints to avoid large payloads for bots with long histories.
- Add a note on WebSocket fallback behavior (polling interval and UX) when the socket is disconnected.

### Questions
- Will the production stack run a single API worker when WebSockets are enabled, or should we plan a brokered pub/sub for multi-worker broadcasts?

### Blocking Issues (if REQUEST CHANGES)
1. **Per-bot cost cap storage is undefined.**
   - You add `/api/bots/{bot_id}/cost-cap`, but the plan doesn’t specify where these overrides live or how `check_usage_cap()` will read them.
   - Please choose one: add explicit columns to `Bot`, store caps inside `personality_config`, or create a dedicated `bot_settings` table, and note how defaults and overrides are resolved.

2. **WebSocket broadcast in production is ambiguous with multiple workers.**
   - The in-memory `ConnectionManager` will only broadcast to clients connected to the same worker process.
   - Please commit to either: single-worker API when WebSockets are enabled, or a shared pub/sub (e.g., Redis) to fan out events across workers, and update the production section accordingly.
