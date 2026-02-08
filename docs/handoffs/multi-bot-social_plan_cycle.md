# Review Cycle: multi-bot-social (plan)

## Metadata
- **Phase:** multi-bot-social
- **Type:** plan
- **Started:** 2026-02-04
- **Lead:** Claude
- **Reviewer:** Codex

## Reference
- Plan: `docs/phases/multi-bot-social.md`

---

## Round 1

### Lead
**Action:** SUBMIT_FOR_REVIEW

Phase 2: Multi-Bot Social plan is ready for review. This phase expands Botastrophic from a single bot to a full social ecosystem.

**Key components:**

1. **5 additional bots** — Marcus (analytical), Luna (creative), Rex (bold), Echo (shy), Sage (wise) with distinct personality configs

2. **Warm memory system** — New `WarmMemory` model storing facts, relationships, opinions. Extraction via cheap model after each heartbeat. Keyword-based filtering for context injection.

3. **Voting system** — New `Vote` model, endpoints for upvote/downvote, new `vote` action type in heartbeat

4. **Pace control** — API endpoints to switch between Slow (4h), Normal (1h), Fast (15min), Turbo (5min). Dynamic scheduler updates.

5. **Follow system** — `Follow` model, endpoints for managing relationships, personalized feed

6. **Seed topics** — 5-10 initial threads loaded on first startup

7. **Dashboard** — Read-only React app with activity feed, thread browser, bot profiles

**Scope boundaries:**
- IN: 6 bots, warm memory, voting, pace control, follows, seeds, basic dashboard
- OUT: Cold memory, web search, reputation effects, embeddings, dashboard config, WebSocket, per-bot pace

**Questions for reviewer:**
1. Is the warm memory schema appropriate for Phase 2?
2. Should voting be a separate action or combined with reply/thread creation?
3. Is the dashboard scope (read-only) appropriate, or should we include any config?

Please review the full plan at `docs/phases/multi-bot-social.md`.

### Reviewer
**Action:** REQUEST_CHANGES

Solid plan and clear scope. I’m requesting a couple clarifications to keep the schema and success criteria testable.

**Blocking issues**
1. **WarmMemory primary key/uniqueness**: Please specify the primary key or uniqueness strategy for `WarmMemory`. Recommendation: one row per bot (`bot_id` as PK or unique), plus `created_at`/`updated_at`. Right now the schema is ambiguous and could allow multiple rows per bot.
2. **Success criteria testability**: “Bots engage with each other (replies to other bots' threads)” is not specific. Please define a concrete check, e.g., “In a 1-hour dev run with seeds + mock, at least one reply where `author_bot_id != thread.author_bot_id` is logged,” or mark it as a manual observation criterion with a runbook.

**Answers to your questions**
1. Warm memory schema: Use one row per bot (bot_id PK/unique) with JSON fields + timestamps. That keeps retrieval simple and avoids joins.
2. Voting action: Keep as a separate action type. It’s simpler to reason about and avoids conflating vote behavior with posting. You can still allow vote + reply in a single heartbeat by returning multiple actions.
3. Dashboard scope: Read-only is appropriate for Phase 2. Config/editing can wait for Phase 4.

**Non-blocking suggestions**
- Add uniqueness constraints for `Vote` (`voter_bot_id`, `target_type`, `target_id`) and `Follow` (`follower_id`, `following_id`) to prevent duplicates.
- Make `WarmMemory.interests` a JSON column (SQLite doesn’t have native list type).

---

## Round 2

### Lead
**Action:** SUBMIT_FOR_REVIEW

Thanks for the thorough review. I've addressed both blocking issues and incorporated all suggestions.

**Changes made to `docs/phases/multi-bot-social.md`:**

1. **WarmMemory primary key** — Updated schema to specify `bot_id` as primary key (one row per bot). Added `created_at` and `updated_at` timestamps. Changed `interests` to JSON type.

2. **Success criteria testability** — Changed vague "bots engage with each other" to specific: "Cross-bot engagement verified: at least 1 reply where `author_bot_id != thread.author_bot_id` after a 1-hour turbo test run with seeds + mock adapter"

3. **Vote uniqueness** — Added unique constraint `(voter_bot_id, target_type, target_id)`

4. **Follow uniqueness** — Added unique constraint `(follower_id, following_id)`

5. **Voting as separate action** — Confirmed in plan (already was separate)

Ready for re-review.

### Reviewer
**Action:** APPROVE

Approved. Blocking items are resolved and the plan is now testable.

---

<!-- CYCLE_STATUS (single source of truth - do not duplicate above) -->
READY_FOR: reviewer
ROUND: 2
STATE: approved
<!-- /CYCLE_STATUS -->
