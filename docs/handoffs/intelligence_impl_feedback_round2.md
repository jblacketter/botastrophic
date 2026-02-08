# Implementation Review: Intelligence

**Reviewer:** Codex
**Date:** 2026-02-06

## Files Reviewed
- api/app/routes/votes.py: 160 lines
- api/app/orchestrator/heartbeat.py: 286 lines
- api/app/memory/extractor.py: 108 lines
- api/app/memory/warm.py: 153 lines
- api/app/orchestrator/prompt_builder.py: 216 lines
- docs/phases/intelligence.md: 361 lines

## Checklist

### Correctness
- [x] Implementation matches the plan
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
- Vote flip handling now adjusts `reputation_score`, `upvotes_received`, and `downvotes_received` consistently in both vote paths.
- Bot roster now includes IDs, and extraction prompt explicitly asks for bot IDs.

### Issues Found
1. **MEDIUM** Relationship history events are still unlikely to be created.
   - Location: `api/app/orchestrator/heartbeat.py:210`, `api/app/memory/extractor.py:9`, `api/app/memory/warm.py:115`
   - Why: `extract_memories()` receives `action_details=result`, which for `reply` and `vote` does not include content or the other bot’s ID. The extraction prompt demands `other_bot_id`, but the LLM is not given a mapping or any IDs to reference. `record_interaction()` increments counts but only appends history when `event` is provided, and it is never passed.
   - Impact: The success criterion “after 10+ interactions, at least one relationship has history events” is not reliably achievable.
   - Suggested fix: Pass richer action context into `extract_memories()` (include reply content and the other bot’s ID), or add an `event` parameter to `record_interaction()` for reply/vote actions so history can be populated without relying on the LLM.

### Suggestions (non-blocking)
- Consider consolidating `_update_author_reputation()` into a shared helper to avoid drift between `votes.py` and `heartbeat.py`.
- Add a small regression test for vote flips and relationship history creation.
