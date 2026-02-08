# Implementation Review: Expansion

**Reviewer:** Codex
**Date:** 2026-02-06

## Files Reviewed
- api/app/routes/stats.py
- api/app/orchestrator/heartbeat.py
- api/app/routes/bots.py
- api/app/routes/moderation.py
- api/app/routes/threads.py
- api/app/bot_loader.py
- api/app/database.py
- dashboard/src/components/ConfigPanel.tsx
- dashboard/src/components/BotCreator.tsx
- dashboard/src/App.tsx

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
- Custom bot persistence via `source` and YAML sync behavior is well defined.
- Auto-moderation hooks and pause logic are integrated cleanly into heartbeat.
- Public API + read-only view are aligned with plan.

### Issues Found
1. **HIGH** `GET /api/stats/analytics` and `GET /api/stats/relationship-graph` will crash due to missing imports.
   - Location: `api/app/routes/stats.py`
   - Why: `Thread`, `Reply`, `Vote`, and `datetime` are referenced but not imported. This causes `NameError` at runtime, breaking analytics and relationship graph features.
   - Suggested fix: Add the missing imports at the top of the file.

2. **MEDIUM** Personality schema is still inconsistent with the new numeric standard.
   - Location: `dashboard/src/components/ConfigPanel.tsx`, `dashboard/src/components/BotCreator.tsx`, `api/app/routes/bots.py`
   - Why: The plan says behavior fields are numeric 0–100, but ConfigPanel still maps `creativity_level` to string labels and writes strings, and BotCreator/CustomBotCreate do not include `creativity_level` at all.
   - Impact: Custom bots created with numeric schema can be overwritten to string values, undermining the standardization decision.
   - Suggested fix: Make `creativity_level` numeric everywhere (ConfigPanel read/write, BotCreator request, CustomBotCreate schema), or formally drop it from the schema across the app.

### Suggestions (non-blocking)
- `MAX_BOT_COUNT` is hardcoded as `12` in `dashboard/src/App.tsx`; consider reading it from `/api/config` to keep UI and backend in sync.
- Add basic tests for `/api/stats/analytics`, `/api/stats/relationship-graph`, and `/api/threads/search` to prevent regressions.
