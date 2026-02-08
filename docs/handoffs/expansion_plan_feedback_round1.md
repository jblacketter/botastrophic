# Plan Review: Expansion

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
- Strong, cohesive Phase 5 scope and a sensible implementation order.
- Public view + exports + graph visualization are a good “expansion” theme.
- Clear success criteria for each major feature.

### Suggested Changes
- Clarify where the max bot count is configured (env var name + config default) and surface it in the dashboard UI as a limit message.
- Add a brief note on how `last_reply_at` is updated for API replies (not just orchestrator replies).
- For auto-moderation, replace “cosine similarity” with a concrete overlap metric if embeddings are explicitly out of scope.

### Questions
- Should public view be `/#/public` only (hash router) or `/public` (history router)? The plan mentions both; pick one to avoid ambiguity.

### Blocking Issues (if REQUEST CHANGES)
1. **Personality schema mismatch for new bots.**
   - The plan’s BotCreator uses numeric `creativity_level` (0–100), but the current system stores `behavior.creativity_level` as `"low|medium|high"` (ConfigPanel writes strings, and prompt_builder assumes that structure). This will cause new bots to render or behave inconsistently in the existing dashboard.
   - Please choose and standardize one schema (string levels or numeric), then specify any required updates to ConfigPanel, BotCreator, and stored personality_config.

2. **Custom bot persistence vs YAML sync on startup.**
   - `sync_bots_to_db()` overwrites personality_config from YAML at startup. The plan doesn’t state how custom bots or admin-edited bots should be preserved across restarts.
   - Please define the persistence rule (e.g., mark DB-created bots as `is_custom`, skip YAML overwrite for DB-managed bots, or move YAML bots into DB once and stop syncing). Without this, customizations can be lost.
