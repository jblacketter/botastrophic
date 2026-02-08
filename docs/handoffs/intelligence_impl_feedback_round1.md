# Implementation Review: Intelligence

**Reviewer:** Codex
**Date:** 2026-02-06

## Files Reviewed
- api/app/orchestrator/heartbeat.py: 274 lines
- api/app/orchestrator/action_parser.py: 95 lines
- api/app/tools/web_search.py: 52 lines
- api/app/memory/cold.py: 113 lines
- api/app/memory/warm.py: 153 lines
- api/app/memory/extractor.py: 107 lines
- api/app/usage.py: 78 lines
- api/app/routes/stats.py: 82 lines
- api/app/routes/votes.py: 144 lines
- api/app/llm/ollama.py: 38 lines
- api/app/orchestrator/prompt_builder.py: 216 lines
- api/app/models/bot.py: 19 lines
- api/app/models/cold_memory.py: 21 lines
- api/app/models/usage.py: 20 lines
- api/app/models/warm_memory.py: 38 lines
- api/templates/system_prompt.txt: 121 lines

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
- Wikipedia tool uses `origin=*` + explicit `User-Agent` and handles empty results cleanly.
- Cold memory compression has a reasonable fallback path if Haiku fails.
- Usage caps are enforced before LLM calls, and usage stats aggregation is straightforward.

### Issues Found
1. **MEDIUM** Vote count fields drift on vote changes.
   - Location: `api/app/routes/votes.py:40`, `api/app/orchestrator/heartbeat.py:26`
   - Why: When a vote changes (e.g., +1 to -1), `reputation_score` uses delta correctly, but `upvotes_received`/`downvotes_received` are only incremented and never decremented. This makes counts inaccurate after vote flips.
   - Suggested fix: Adjust counts based on old vs new value (decrement prior bucket, increment new bucket), or recompute counts from `Vote` for the author when a change is detected.

2. **MEDIUM** Relationship keys mix bot IDs and bot names, causing duplicate entries and missed interaction history.
   - Location: `api/app/memory/extractor.py:24`, `api/app/memory/warm.py:58`, `api/app/memory/warm.py:115`
   - Why: LLM extraction uses `other_bot_name`, while `record_interaction()` uses `other_bot_id`. `update_warm_memory()` merges by `bot` key, so the same bot can appear twice (name vs id) and interaction counts/history won’t unify.
   - Suggested fix: Standardize on bot ID in both extraction and interaction tracking (include name as a separate field if needed), or map IDs to names before writing relationships.

### Suggestions (non-blocking)
- Consider moving pricing constants in `api/app/usage.py` to config to avoid drift as provider pricing changes.
- Add basic tests for vote updates (especially vote flips) and warm relationship merging to prevent regressions.
