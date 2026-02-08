# Implementation Log: Intelligence

**Started:** 2026-02-05
**Lead:** Claude
**Plan:** docs/phases/intelligence.md

## Progress

### Session 1 - 2026-02-05
- [x] Feature 1: Web Search Tool (Wikipedia API)
- [x] Feature 2: Cold Memory Tier
- [x] Feature 3: Relationship Evolution
- [x] Feature 4: Ollama Adapter
- [x] Feature 5: Reputation System
- [x] Feature 6: Cost Tracking

## Files Created
- `api/app/tools/__init__.py` - Tools package init
- `api/app/tools/web_search.py` - WikipediaSearchTool class
- `api/app/models/cold_memory.py` - ColdMemory SQLAlchemy model
- `api/app/models/usage.py` - TokenUsage SQLAlchemy model
- `api/app/memory/cold.py` - Cold memory compression logic
- `api/app/usage.py` - Cost tracking, daily caps, usage recording
- `api/app/routes/stats.py` - GET /api/stats/usage endpoint

## Files Modified
- `api/app/orchestrator/heartbeat.py` - Web search execution, reputation updates, usage caps, cold compression, interaction tracking
- `api/app/orchestrator/action_parser.py` - (no changes needed, web_search already supported)
- `api/app/orchestrator/prompt_builder.py` - Added reputation_score template variable
- `api/app/orchestrator/scheduler.py` - Added weekly cold compression cron job (Sunday 3am)
- `api/app/memory/warm.py` - Relationship history/interaction_count/last_interaction fields, record_interaction helper
- `api/app/memory/extractor.py` - Enhanced extraction prompt with relationship history
- `api/app/models/bot.py` - Added reputation_score, upvotes_received, downvotes_received columns
- `api/app/models/__init__.py` - Exported ColdMemory, TokenUsage
- `api/app/routes/bots.py` - Reputation fields in BotResponse
- `api/app/routes/votes.py` - _update_author_reputation on vote cast
- `api/app/llm/ollama.py` - Full implementation replacing stub
- `api/app/main.py` - Registered stats router
- `api/templates/system_prompt.txt` - Added web_search action docs, reputation display
- `docker-compose.yml` - Added ollama service + volume
- `api/requirements.txt` - Added httpx>=0.27.0

## Decisions Made
- Reputation update logic duplicated in both heartbeat.py and votes.py to cover bot-initiated votes (heartbeat) and API-initiated votes (route)
- Used vote delta calculation for reputation updates when changing an existing vote
- record_interaction() called on reply and vote to track cross-bot interactions
- Cold compression fallback: concatenate top facts if LLM summarization fails
- Ollama timeout set to 120s (local models can be slow on first run)

## Issues Encountered
- DB migration needed: SQLAlchemy `create_tables()` doesn't add columns to existing tables. Used manual `ALTER TABLE` for new Bot columns.
- Wikipedia 403: Required `origin=*` parameter and descriptive User-Agent header.
- BotResponse missing reputation fields in `get_bot` endpoint (fixed — `replace_all` only matched `list_bots` due to indentation differences).

## Review Round 1 - Codex Feedback (2026-02-06)
**Verdict:** REQUEST CHANGES

### Fixes Applied:
1. **Vote count drift** — Refactored `_update_author_reputation()` in both `votes.py` and `heartbeat.py` to accept `old_value` param. On vote flip, old bucket is decremented and new bucket incremented. Tested: upvote→downvote correctly adjusts both counters.
2. **Relationship key mismatch** — Standardized on bot IDs for relationship keys. Updated bot roster to show IDs (e.g. "Ada (id: ada_001)"), extraction prompt instructs LLM to use bot IDs, and added explicit instruction: "use the bot's ID, not their display name."

## Review Round 2 - Codex Feedback (2026-02-06)
**Verdict:** REQUEST CHANGES

### Fixes Applied:
1. **Relationship history events never created** — `record_interaction()` was called without `event` param, so history arrays stayed empty. Added descriptive event strings to all `record_interaction()` calls in `heartbeat.py` for both reply and vote actions. Also enriched action result dicts with `other_bot_id` for richer extraction context. Tested: history events now appear in warm memory.
