# Review Cycle: Expansion (Plan)

**Phase:** Expansion (Phase 5)
**Type:** Plan Review
**Lead:** Claude
**Reviewer:** Codex

## Round 1
- **Date:** 2026-02-06
- **Plan:** `docs/phases/expansion.md`
- **Status:** REQUEST CHANGES
- **Feedback:** `docs/handoffs/expansion_plan_feedback_round1.md`
- **Blocking issues:**
  1. Personality schema mismatch (numeric vs string `creativity_level`)
  2. Custom bot persistence — `sync_bots_to_db()` overwrites all bots from YAML
- **Fixes applied:**
  - Standardized on numeric 0-100 behavior values, documented full `personality_config` structure
  - Added `source` column ("yaml"/"custom") to Bot model, `sync_bots_to_db()` skips custom bots
  - Clarified `MAX_BOT_COUNT` env var, `last_reply_at` update paths, Jaccard metric, hash routing

## Round 2
- **Date:** 2026-02-06
- **Plan:** `docs/phases/expansion.md` (revised)
- **Status:** APPROVED
- **Feedback:** `docs/handoffs/expansion_plan_feedback.md`
- **Non-blocking suggestions:**
  1. Add UI warning for YAML bots: "Edits reset on restart unless YAML is updated"
  2. Include `MAX_BOT_COUNT` limit in API error responses for better UI feedback
